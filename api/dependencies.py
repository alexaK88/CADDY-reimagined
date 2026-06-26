"""
FastAPI dependencies.

This module exposes the shared in-memory MissionBackend instance stored on the
FastAPI application state.
"""

from __future__ import annotations

from fastapi import Request

from mission_backend.mission_backend import MissionBackend


def get_mission_backend(request: Request) -> MissionBackend:
    """
    Return the application-level MissionBackend instance.
    """

    return request.app.state.mission_backend