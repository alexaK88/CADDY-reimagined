"""
Mission runtime routes.

These endpoints allow the UI to start and stop a live mission simulation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_mission_runtime
from mission_runtime.mission_runtime import MissionRuntimeManager
from mission_runtime.schemas import (MissionRuntimeStatus, StartRuntimeRequest, StopRuntimeRequest, )

router = APIRouter(prefix="/runtime", tags=["runtime"], )


@router.post("/start", response_model=MissionRuntimeStatus)
async def start_runtime(request: StartRuntimeRequest,
        runtime: MissionRuntimeManager = Depends(get_mission_runtime), ) -> MissionRuntimeStatus:
    """
    Start the live mission runtime.
    """

    try:
        return await runtime.start(scenario=request.scenario, mission_id=request.mission_id,
            tick_interval_s=request.tick_interval_s, )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/stop", response_model=MissionRuntimeStatus)
async def stop_runtime(request: StopRuntimeRequest,
        runtime: MissionRuntimeManager = Depends(get_mission_runtime), ) -> MissionRuntimeStatus:
    """
    Stop the live mission runtime.
    """

    try:
        return await runtime.stop(reason=request.reason)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/status", response_model=MissionRuntimeStatus)
def get_runtime_status(runtime: MissionRuntimeManager = Depends(get_mission_runtime), ) -> MissionRuntimeStatus:
    """
    Return current live runtime status.
    """

    return runtime.get_status()
