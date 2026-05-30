import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

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
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(log_requests)

    app.include_router(api_router)
    return app


app = create_app()
