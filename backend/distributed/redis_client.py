from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from backend.config import settings
from backend.telemetry.metrics import metrics_store


class RedisUnavailable(RuntimeError):
    pass


class RedisCoordinator:
    def __init__(self) -> None:
        self._client = None
        self.last_error: str | None = None

    async def connect(self):
        if self._client is not None:
            try:
                await self._client.ping()
                metrics_store.record_dependency("redis", True)
                return self._client
            except Exception:
                await self.close()
        if not settings.redis_url:
            raise RedisUnavailable("REDIS_URL is required for distributed coordination")
        import redis.asyncio as redis

        for attempt in range(1, settings.dependency_connect_attempts + 1):
            try:
                metrics_store.record_dependency_reconnect("redis", "attempt")
                self._client = redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=settings.dependency_probe_timeout_seconds,
                    socket_timeout=settings.dependency_probe_timeout_seconds,
                    health_check_interval=15,
                )
                await self._client.ping()
                self.last_error = None
                metrics_store.record_dependency("redis", True)
                metrics_store.record_dependency_reconnect("redis", "ok")
                return self._client
            except Exception as exc:
                self.last_error = str(exc)
                metrics_store.record_dependency("redis", False)
                metrics_store.record_dependency_reconnect("redis", "failed")
                await self.close()
                if attempt == settings.dependency_connect_attempts:
                    raise RedisUnavailable(f"Redis connection failed after {attempt} attempts: {exc}") from exc
                await asyncio.sleep(settings.dependency_retry_seconds)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @asynccontextmanager
    async def client(self) -> AsyncIterator:
        try:
            yield await self.connect()
        except RedisUnavailable:
            raise
        except Exception as exc:
            await self.close()
            self.last_error = str(exc)
            metrics_store.record_dependency("redis", False)
            metrics_store.record_dependency_reconnect("redis", "dropped")
            raise RedisUnavailable(str(exc)) from exc

    async def available(self) -> bool:
        try:
            async with self.client() as client:
                await client.ping()
            return True
        except Exception:
            return False

    async def ensure_consumer_group(self, stream: str | None = None, group: str | None = None) -> None:
        stream_name = stream or settings.inference_stream
        group_name = group or settings.inference_consumer_group
        async with self.client() as client:
            try:
                await client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
            except Exception as exc:
                if "BUSYGROUP" not in str(exc):
                    raise
            try:
                pending = await client.xpending(stream_name, group_name)
                count = int(pending.get("pending", 0) if isinstance(pending, dict) else 0)
                metrics_store.record_redis_stream_lag(stream_name, group_name, count)
                stream_info = await client.xinfo_stream(stream_name)
                metrics_store.record_redis_stream_length(stream_name, int(stream_info.get("length", 0)))
            except Exception:
                pass

    async def recover_pending_messages(self, stream: str | None = None, group: str | None = None, *, count: int = 100) -> int:
        stream_name = stream or settings.inference_stream
        group_name = group or settings.inference_consumer_group
        async with self.client() as client:
            try:
                pending = await client.xpending_range(stream_name, group_name, min="-", max="+", count=count)
            except Exception:
                return 0
            recovered = 0
            for entry in pending or []:
                message_id = entry.get("message_id")
                if not message_id:
                    continue
                try:
                    await client.xclaim(stream_name, group_name, "recovery-worker", min_idle_time=0, message_ids=[message_id])
                    recovered += 1
                except Exception:
                    continue
            if recovered:
                metrics_store.record_recovery_action("redis_pending_claim", "ok")
            return recovered

    async def record_checkpoint(self, name: str, value: str) -> None:
        async with self.client() as client:
            await client.hset(settings.inference_checkpoint_hash, name, value)


redis_coordinator = RedisCoordinator()
