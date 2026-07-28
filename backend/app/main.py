"""FastAPI application entrypoint for the Chat With Your Docs backend."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import documents, health, knowledge_index, query
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    configure_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        """Map domain errors to meaningful HTTP responses (FR-20)."""
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(knowledge_index.router, prefix=settings.api_prefix)
    app.include_router(documents.router, prefix=settings.api_prefix)
    app.include_router(query.router, prefix=settings.api_prefix)
    return app


app = create_app()
