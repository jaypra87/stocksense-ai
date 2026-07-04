import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging

logger = logging.getLogger("stocksense.request")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield


async def log_requests(request: Request, call_next):
    """Log method, path, status, and duration for every request."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


def make_security_headers(production: bool) -> dict[str, str]:
    """Defensive headers for every API response. The API serves JSON (plus the
    Swagger docs), so a deny-by-default CSP is safe; docs pages override
    nothing because browsers only apply frame/script rules where relevant."""
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Cache-Control": "no-store",
    }
    if production:
        headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return headers


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="StockSense AI API",
        version="0.1.0",
        description="Educational stock analytics. Not financial advice.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.middleware("http")(log_requests)

    security_headers = make_security_headers(settings.environment == "production")

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        for key, value in security_headers.items():
            response.headers.setdefault(key, value)
        return response

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Log the real error server-side; never leak internals to the client.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.include_router(api_router)
    return app


app = create_app()
