"""FastAPI application entrypoint for the Chat With Your Docs backend."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import documents, health, knowledge_index, query
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.rag.embeddings import get_embeddings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Preload the embedding weights so the first upload is not penalised (FR-5).

    Loading runs on a worker thread to keep the event loop free, but startup
    waits for it so a ready server always has the model in memory. A failure is
    logged rather than fatal: the rest of the API stays usable and indexing
    surfaces the error per request when the weights are unavailable.
    """
    settings = get_settings()
    if settings.warm_embeddings_on_startup:
        try:
            await asyncio.to_thread(get_embeddings)
            logger.info("Preloaded embedding model '%s'.", settings.embedding_model)
        except Exception:
            logger.exception(
                "Failed to preload embedding model '%s'; it will be loaded on first use.",
                settings.embedding_model,
            )
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    configure_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

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
