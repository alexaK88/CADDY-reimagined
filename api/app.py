"""
FastAPI application factory for the autonomous diver companion backend.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from api.routes import health, missions
from mission_backend.mission_backend import MissionBackend


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Initialize and clean up application-level resources.
    """

    app.state.mission_backend = MissionBackend()

    yield

    app.state.mission_backend.reset()


def create_app() -> FastAPI:
    """
    Create the FastAPI application.
    """

    app = FastAPI(title="Autonomous Diver Companion Mission API",
        description=("HTTP API for mission backend state, mission events, and mission "
                     "summaries."), version="0.1.0", lifespan=lifespan, )

    app.include_router(health.router)
    app.include_router(missions.router)

    return app


app = create_app()