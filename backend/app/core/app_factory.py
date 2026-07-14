from fastapi import FastAPI

from app.core.config import Settings
from app.middleware.cors import add_cors_middleware
from app.middleware.secure_headers import add_secure_headers_middleware
from app.middleware.exception_handlers import register_exception_handlers
from app.api.v1.router import api_router_v1
from app.core.logging_setup import setup_logging


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    This function is the single entry point used by `backend/main.py`.

    Returns:
        FastAPI: Configured FastAPI app.
    """
    settings = Settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
    )

    add_cors_middleware(app, settings.cors_origins)
    add_secure_headers_middleware(app)
    register_exception_handlers(app)

    # API
    app.include_router(api_router_v1, prefix=settings.api_prefix)

    return app

