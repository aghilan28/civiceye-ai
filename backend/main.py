from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from backend.api.routes import router
from backend.api.auth_routes import router as auth_router
from backend.api.distributed_routes import router as distributed_router
from backend.api.enterprise_routes import router as enterprise_router
from backend.api.operations_routes import router as operations_router
from backend.config import settings
from backend.database.postgres import postgres_pool
from backend.distributed.redis_client import redis_coordinator
from backend.distributed.orchestration import distributed_orchestrator
from backend.inference.model_loader import model_loader
from backend.security.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from backend.telemetry.logger import configure_logging


configure_logging()
app = FastAPI(title=settings.app_name, version=settings.api_version)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(auth_router)
app.include_router(operations_router)
app.include_router(enterprise_router)
app.include_router(distributed_router)


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.on_event("startup")
async def startup() -> None:
    await postgres_pool.connect()
    if settings.redis_url:
        try:
            await redis_coordinator.connect()
            await distributed_orchestrator.startup_recovery()
        except Exception as exc:
            if settings.redis_url:
                raise RuntimeError(f"Redis startup validation failed: {exc}") from exc
    else:
        await distributed_orchestrator.expire_workers()
        await distributed_orchestrator.recover_timeouts()
        await distributed_orchestrator.recover_orphaned_jobs()
    if settings.resolved_weights_path.exists():
        model_loader.load()


@app.on_event("shutdown")
async def shutdown() -> None:
    await redis_coordinator.close()
    await postgres_pool.close()
