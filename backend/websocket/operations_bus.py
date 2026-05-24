from __future__ import annotations

import asyncio
import json
from collections import OrderedDict
from datetime import datetime, timezone
from collections import defaultdict, deque
from time import time
from uuid import uuid4

from fastapi import WebSocket

from backend.config import settings
from backend.distributed.redis_client import RedisUnavailable, redis_coordinator
from backend.security.auth import websocket_principal
from backend.telemetry.metrics import metrics_store


class OperationsEventBus:
    def __init__(self) -> None:
        self._sockets: dict[str, WebSocket] = {}
        self._socket_meta: dict[str, dict] = {}
        self._event_count = 0
        self._last_event_at: datetime | None = None
        self._dedupe: OrderedDict[str, float] = OrderedDict()
        self._subscriber_task: asyncio.Task | None = None
        self._redis_events = 0
        self._local_events = 0
        self._message_hits: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=settings.websocket_max_messages_per_minute * 2))

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        principal = websocket_principal(websocket)
        if settings.require_auth and principal is None:
            await websocket.send_json({"type": "error", "error": "websocket_auth_required"})
            await websocket.close(code=4401)
            return ""
        session_id = str(uuid4())
        municipality_id = websocket.query_params.get("municipality_id") or (principal.municipality_id if principal else None)
        if principal and websocket.query_params.get("municipality_id") and principal.municipality_id and websocket.query_params.get("municipality_id") != principal.municipality_id:
            await websocket.send_json({"type": "error", "error": "websocket_tenant_mismatch"})
            await websocket.close(code=4403)
            return ""
        channels = [
            channel.strip()
            for channel in (websocket.query_params.get("channels") or "municipal-operations").split(",")
            if channel.strip()
        ]
        self._sockets[session_id] = websocket
        self._socket_meta[session_id] = {
            "municipality_id": municipality_id,
            "channels": channels,
            "connected_at": datetime.now(timezone.utc),
            "last_seen_at": datetime.now(timezone.utc),
            "principal": principal.user_id if principal else None,
            "session_expires_at": principal.expires_at if principal else None,
        }
        await self._ensure_subscriber()
        await websocket.send_json(
            {
                "type": "connected",
                "channel": "municipal-operations",
                "session_id": session_id,
                "region": settings.websocket_region,
                "node_id": settings.websocket_node_id,
            }
        )
        return session_id

    def disconnect(self, websocket_or_session) -> None:
        if isinstance(websocket_or_session, str):
            session_id = websocket_or_session
        else:
            session_id = next((key for key, socket in self._sockets.items() if socket is websocket_or_session), "")
        if session_id:
            self._sockets.pop(session_id, None)
            self._socket_meta.pop(session_id, None)

    async def broadcast(self, event: dict, *, distributed: bool = True) -> None:
        enriched = self._enrich_event(event)
        if distributed:
            try:
                async with redis_coordinator.client() as client:
                    await client.publish(settings.websocket_event_channel, json.dumps(enriched, default=str))
                    self._redis_events += 1
                    return
            except Exception:
                pass
        await self._broadcast_local(enriched)

    async def heartbeat(self, session_id: str) -> dict:
        if self._rate_limited(session_id):
            return {"type": "error", "error": "websocket_rate_limited", "session_id": session_id}
        if session_id in self._socket_meta:
            self._socket_meta[session_id]["last_seen_at"] = datetime.now(timezone.utc)
        return {"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat(), "session_id": session_id}

    async def cleanup_stale(self, max_idle_seconds: int = 90) -> int:
        now = datetime.now(timezone.utc)
        stale = [
            session_id
            for session_id, meta in self._socket_meta.items()
            if (now - meta["last_seen_at"]).total_seconds() > max_idle_seconds
            or (meta.get("session_expires_at") and now >= meta["session_expires_at"])
            or (now - meta["connected_at"]).total_seconds() > settings.websocket_session_ttl_seconds
        ]
        for session_id in stale:
            socket = self._sockets.get(session_id)
            if socket is not None:
                try:
                    await socket.close(code=1001)
                except Exception:
                    pass
            self.disconnect(session_id)
        return len(stale)

    async def _broadcast_local(self, event: dict) -> None:
        if self._seen(event["event_id"]):
            return
        self._event_count += 1
        self._local_events += 1
        self._last_event_at = datetime.now(timezone.utc)
        metrics_store.record_websocket(str(event.get("type", "unknown")), settings.websocket_region, len(self._sockets))
        dead: list[str] = []
        for session_id, websocket in list(self._sockets.items()):
            meta = self._socket_meta.get(session_id, {})
            if not self._matches(meta, event):
                continue
            try:
                await websocket.send_json(event)
            except Exception:
                dead.append(session_id)
        for session_id in dead:
            self.disconnect(session_id)

    async def _ensure_subscriber(self) -> None:
        if self._subscriber_task and not self._subscriber_task.done():
            return
        if not settings.redis_url:
            return
        self._subscriber_task = asyncio.create_task(self._subscribe_redis())

    async def _subscribe_redis(self) -> None:
        try:
            async with redis_coordinator.client() as client:
                pubsub = client.pubsub()
                await pubsub.subscribe(settings.websocket_event_channel)
                async for message in pubsub.listen():
                    if message.get("type") != "message":
                        continue
                    try:
                        event = json.loads(message["data"])
                    except Exception:
                        continue
                    await self._broadcast_local(event)
        except (RedisUnavailable, asyncio.CancelledError):
            return
        except Exception:
            return

    def _enrich_event(self, event: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "event_id": event.get("event_id") or str(uuid4()),
            "timestamp": event.get("timestamp") or now,
            "origin_node": settings.websocket_node_id,
            "region": event.get("region") or settings.websocket_region,
            "municipality_id": event.get("municipality_id")
            or event.get("municipalityId")
            or (event.get("incident") or {}).get("municipality_id")
            or (event.get("event") or {}).get("municipality_id"),
            **event,
        }

    def _seen(self, event_id: str) -> bool:
        now = datetime.now(timezone.utc).timestamp()
        while self._dedupe and now - next(iter(self._dedupe.values())) > 300:
            self._dedupe.popitem(last=False)
        if event_id in self._dedupe:
            return True
        self._dedupe[event_id] = now
        return False

    def _rate_limited(self, session_id: str) -> bool:
        now = time()
        hits = self._message_hits[session_id]
        while hits and now - hits[0] > 60:
            hits.popleft()
        if len(hits) >= settings.websocket_max_messages_per_minute:
            metrics_store.record_websocket("rate_limited", settings.websocket_region, len(self._sockets))
            return True
        hits.append(now)
        return False

    def _matches(self, meta: dict, event: dict) -> bool:
        municipality_id = event.get("municipality_id") or event.get("municipalityId")
        if meta.get("municipality_id") and municipality_id and meta["municipality_id"] != municipality_id:
            return False
        event_channel = event.get("channel") or event.get("type")
        channels = set(meta.get("channels") or [])
        return not channels or "municipal-operations" in channels or event_channel in channels

    def health(self) -> dict:
        by_region = {settings.websocket_region: len(self._sockets)}
        return {
            "connected_clients": len(self._sockets),
            "events_published": self._event_count,
            "last_event_at": self._last_event_at.isoformat() if self._last_event_at else None,
            "redis_events": self._redis_events,
            "local_events": self._local_events,
            "dedupe_window": len(self._dedupe),
            "region": settings.websocket_region,
            "node_id": settings.websocket_node_id,
            "regional_clients": by_region,
        }


operation_bus = OperationsEventBus()
