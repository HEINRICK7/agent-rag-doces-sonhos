"""FastAPI application factory."""

import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.bootstrap import build_container
from app.shared.configuration.logging import configure_logging
from app.shared.configuration.settings import Settings, get_settings
from app.shared.domain.exceptions import InfrastructureError, ValidationError
from app.shared.entrypoints.api.health import router as health_router
from app.users.domain.exceptions import EmailAlreadyExistsError, UserNotFoundError
from app.users.entrypoints.api.router import router as users_router

logger = logging.getLogger(__name__)


def _error_response(request: Request, code: str, message: str, status_code: int) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "correlation_id": correlation_id,
            }
        },
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an application without opening a database connection."""

    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)
    container, engine, infrastructure_health = build_container(app_settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await infrastructure_health.close()
        await engine.dispose()

    app = FastAPI(
        title=app_settings.app_name,
        version="0.1.0",
        docs_url="/docs" if app_settings.docs_enabled else None,
        redoc_url="/redoc" if app_settings.docs_enabled else None,
        openapi_url="/openapi.json" if app_settings.docs_enabled else None,
        lifespan=lifespan,
    )
    app.state.container = container
    app.state.engine = engine
    app.state.infrastructure_health = infrastructure_health

    if app_settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=app_settings.cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH"],
            allow_headers=["Content-Type", "X-Correlation-ID"],
        )

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        request.state.correlation_id = correlation_id
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "request method=%s path=%s status=%s duration_ms=%.2f correlation_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            correlation_id,
        )
        return response

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(request: Request, exc: UserNotFoundError) -> JSONResponse:
        return _error_response(request, exc.code, exc.message, 404)

    @app.exception_handler(EmailAlreadyExistsError)
    async def duplicate_email_handler(
        request: Request, exc: EmailAlreadyExistsError
    ) -> JSONResponse:
        return _error_response(request, exc.code, exc.message, 409)

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        message = str(exc) if exc.args else exc.message
        return _error_response(request, exc.code, message, 422)

    @app.exception_handler(InfrastructureError)
    async def infrastructure_handler(request: Request, exc: InfrastructureError) -> JSONResponse:
        logger.exception("infrastructure error correlation_id=%s", request.state.correlation_id)
        return _error_response(request, exc.code, exc.message, 500)

    @app.exception_handler(Exception)
    async def unexpected_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unexpected error correlation_id=%s", request.state.correlation_id)
        return _error_response(request, "INTERNAL_ERROR", "Erro interno.", 500)

    app.include_router(health_router, prefix=app_settings.api_prefix)
    app.include_router(users_router, prefix=app_settings.api_prefix)
    return app


app = create_app()
