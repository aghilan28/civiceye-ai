from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg

from backend.config import settings
from backend.telemetry.metrics import metrics_store


class DatabaseUnavailable(RuntimeError):
    pass


class PostgresPool:
    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None
        self.last_error: str | None = None

    async def connect(self) -> None:
        if not settings.database_url:
            return
        if self._pool is None:
            for attempt in range(1, settings.dependency_connect_attempts + 1):
                try:
                    metrics_store.record_dependency_reconnect("postgres", "attempt")
                    self._pool = await asyncpg.create_pool(
                        dsn=settings.database_url,
                        min_size=1,
                        max_size=10,
                        command_timeout=30,
                        timeout=settings.dependency_probe_timeout_seconds,
                    )
                    async with self._pool.acquire() as connection:
                        await connection.fetchval("SELECT 1")
                    self.last_error = None
                    metrics_store.record_dependency("postgres", True)
                    metrics_store.record_dependency_reconnect("postgres", "ok")
                    return
                except Exception as exc:
                    self.last_error = str(exc)
                    metrics_store.record_dependency("postgres", False)
                    metrics_store.record_dependency_reconnect("postgres", "failed")
                    if self._pool is not None:
                        await self._pool.close()
                        self._pool = None
                    if attempt == settings.dependency_connect_attempts:
                        raise DatabaseUnavailable(f"Postgres connection failed after {attempt} attempts: {exc}") from exc
                    await asyncio.sleep(settings.dependency_retry_seconds)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        if self._pool is None:
            await self.connect()
        if self._pool is None:
            raise DatabaseUnavailable("DATABASE_URL is required for civic operations persistence")
        try:
            async with self._pool.acquire() as connection:
                metrics_store.record_dependency("postgres", True)
                yield connection
        except (asyncpg.InterfaceError, asyncpg.PostgresConnectionError) as exc:
            self.last_error = str(exc)
            metrics_store.record_dependency("postgres", False)
            metrics_store.record_dependency_reconnect("postgres", "dropped")
            await self.close()
            raise DatabaseUnavailable(f"Postgres connection dropped: {exc}") from exc


postgres_pool = PostgresPool()
