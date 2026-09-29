"""Health check endpoint (FR-21)."""

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str | bool]:
    """Report basic service health and which optional features are available.

    ``tts_enabled`` lets the client hide or disable the spoken-answer control
    when the deployment has no speech engine configured.
    """
    return {"status": "ok", "tts_enabled": settings.tts_enabled}
