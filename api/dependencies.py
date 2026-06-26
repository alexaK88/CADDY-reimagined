"""
FastAPI dependencies.

This module exposes the shared in-memory MissionBackend instance stored on the
FastAPI application state.
"""

from __future__ import annotations

from fastapi import Request

from mission_backend.mission_backend import MissionBackend
from mission_runtime.mission_runtime import MissionRuntimeManager


def get_mission_backend(request: Request) -> MissionBackend:
    """
    Return the application-level MissionBackend instance.
    """

    return request.app.state.mission_backend

def get_mission_runtime(request: Request) -> MissionRuntimeManager:
    """
    Return the applciation-level MissionRuntimeManager instance.
    """
    return request.app.state.mission_runtime
