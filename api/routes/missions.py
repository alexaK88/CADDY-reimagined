"""
Mission backend routes.

These endpoints expose the in-memory MissionBackend through HTTP. They do not
contain mission decision logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_mission_backend
from api.schemas import (ApiMessage, MissionSnapshotResponse, MissionSummaryResponse, StartMissionRequest, )
from mission_backend.mission_backend import MissionBackend
from mission_backend.schemas import MissionSnapshot
from mission_logging.schemas import MissionEvent

router = APIRouter(prefix="/missions", tags=["missions"], )


@router.post("/start", response_model=MissionSnapshotResponse)
def start_mission(request: StartMissionRequest,
        backend: MissionBackend = Depends(get_mission_backend), ) -> MissionSnapshotResponse:
    """
    Start a new mission run.
    """

    try:
        snapshot = backend.start_mission(scenario=request.scenario, mission_id=request.mission_id, )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return MissionSnapshotResponse(snapshot=snapshot)


@router.post("/events", response_model=MissionSnapshotResponse)
def ingest_event(event: MissionEvent,
        backend: MissionBackend = Depends(get_mission_backend), ) -> MissionSnapshotResponse:
    """
    Ingest one mission event into the active mission.
    """

    try:
        snapshot = backend.ingest_event(event)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return MissionSnapshotResponse(snapshot=snapshot)


@router.get("/snapshot", response_model=MissionSnapshotResponse)
def get_snapshot(backend: MissionBackend = Depends(get_mission_backend), ) -> MissionSnapshotResponse:
    """
    Return the current mission snapshot.
    """

    try:
        snapshot = backend.get_snapshot()
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return MissionSnapshotResponse(snapshot=snapshot)


@router.get("/summary", response_model=MissionSummaryResponse)
def get_summary(backend: MissionBackend = Depends(get_mission_backend), ) -> MissionSummaryResponse:
    """
    Return a compact mission summary.
    """

    try:
        summary = backend.get_summary()
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return MissionSummaryResponse(summary=summary)


@router.get("/events", response_model=list[MissionEvent])
def get_events(backend: MissionBackend = Depends(get_mission_backend), ) -> list[MissionEvent]:
    """
    Return all stored mission events.
    """

    try:
        return backend.get_events()
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/events/recent", response_model=list[MissionEvent])
def get_recent_events(limit: int = Query(default=10, ge=1, le=500),
        backend: MissionBackend = Depends(get_mission_backend), ) -> list[MissionEvent]:
    """
    Return the most recent mission events.
    """

    try:
        return backend.get_recent_events(limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/finish", response_model=MissionSnapshotResponse)
def finish_mission(backend: MissionBackend = Depends(get_mission_backend), ) -> MissionSnapshotResponse:
    """
    Mark the active mission as completed.
    """

    try:
        snapshot = backend.finish_mission()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return MissionSnapshotResponse(snapshot=snapshot)


@router.post("/abort", response_model=MissionSnapshotResponse)
def abort_mission(backend: MissionBackend = Depends(get_mission_backend), ) -> MissionSnapshotResponse:
    """
    Mark the active mission as aborted.
    """

    try:
        snapshot = backend.abort_mission()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return MissionSnapshotResponse(snapshot=snapshot)


@router.post("/reset", response_model=ApiMessage)
def reset_backend(backend: MissionBackend = Depends(get_mission_backend), ) -> ApiMessage:
    """
    Reset the in-memory mission backend.
    """

    backend.reset()

    return ApiMessage(message="Mission backend reset.")
