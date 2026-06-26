"""
Health-check routes.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"], )


@router.get("")
def health_check() -> dict[str, str]:
    """
    Basic health check for the API process.
    """

    return {
        "status": "ok",
        "service": "autonomous-diver-companion-api", }
