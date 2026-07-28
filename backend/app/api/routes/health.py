"""Health check endpoint (FR-21)."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Report basic service health for monitoring."""
    return {"status": "ok"}
