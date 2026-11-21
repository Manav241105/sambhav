"""FastAPI application factory."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from api.events import hub
from api.routers import analytics, auth, bookings, chat, conversations, dashboard, realtime, vehicles, webhooks
from core.logging import configure_logging
from core.settings import get_settings
from db.base import iso_local, utcnow
from db.session import get_engine, get_sessionmaker

log = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await hub.start()
    loop_task = None
    if settings.enable_background_diagnosis and settings.env != "test":
        from services.diagnosis import background_loop

        loop_task = asyncio.create_task(background_loop())
        log.info("Background diagnosis every %s min", settings.diagnosis_interval_minutes)
    log.info("AutoPredict API ready (env=%s, db=%s)", settings.env, settings.database_url.split("://")[0])
    yield
    if loop_task:
        loop_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await loop_task
    await hub.stop()
    await get_engine().dispose()


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(
        title="AutoPredict API",
        version="0.7.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.env != "prod" else None,
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    for module in (auth, vehicles, bookings, dashboard, analytics, conversations, chat, realtime, webhooks):
        app.include_router(module.router)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        db_ok = True
        try:
            async with get_sessionmaker()() as session:
                await session.execute(text("SELECT 1"))
        except Exception:
            db_ok = False
        return {"status": "healthy" if db_ok else "degraded", "database": db_ok, "time": iso_local(utcnow())}

    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {"service": "AutoPredict API", "docs": "/docs", "health": "/health"}

    return app
