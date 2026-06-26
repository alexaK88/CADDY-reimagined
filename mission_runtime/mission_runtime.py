"""
Live mission runtime manager.

This layer runs the mission simulation continuously until the operator stops it
from the API/UI.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from mission_backend.mission_backend import MissionBackend
from mission_logging.mission_logger import MissionLogger
from mission_runtime.schemas import (MissionRuntimeState, MissionRuntimeStatus, )


class MissionRuntimeManager:
    """
    Controls one live mission simulation task.

    The runtime manager owns the background task, stop signal, runtime status,
    and mission logger. It updates MissionBackend as mission events are produced.
    """

    def __init__(self, backend: MissionBackend):
        self._backend = backend

        self._state = MissionRuntimeState.IDLE
        self._mission_id: str | None = None
        self._scenario: str | None = None

        self._started_at_utc: datetime | None = None
        self._stopped_at_utc: datetime | None = None

        self._events_processed = 0
        self._log_path: str | None = None
        self._last_error: str | None = None

        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self,
            scenario: str,
            mission_id: str | None = None,
            tick_interval_s: float = 1.0, ) -> MissionRuntimeStatus:
        """
        Start a live mission simulation.
        """

        if self._state == MissionRuntimeState.RUNNING:
            raise RuntimeError("mission runtime is already running")

        if not scenario:
            raise ValueError("scenario must not be empty")

        self._mission_id = mission_id or str(uuid4())
        self._scenario = scenario
        self._started_at_utc = datetime.now(timezone.utc)
        self._stopped_at_utc = None
        self._events_processed = 0
        self._last_error = None

        self._log_path = str(Path("mission_logs") / f"{self._mission_id}_mission_log.log")

        self._stop_event.clear()

        self._backend.start_mission(scenario=scenario, mission_id=self._mission_id, )

        self._state = MissionRuntimeState.RUNNING

        self._task = asyncio.create_task(
            self._run_loop(scenario=scenario, tick_interval_s=tick_interval_s, log_path=self._log_path, ))

        return self.get_status()

    async def stop(self, reason: str = "Operator ended the mission.", ) -> MissionRuntimeStatus:
        """
        Stop the running mission simulation.
        """

        if self._state != MissionRuntimeState.RUNNING:
            raise RuntimeError("mission runtime is not running")

        self._state = MissionRuntimeState.STOPPING
        self._stop_event.set()

        if self._task is not None:
            await self._task

        self._stopped_at_utc = datetime.now(timezone.utc)
        self._state = MissionRuntimeState.COMPLETED

        self._backend.finish_mission()

        return self.get_status()

    def get_status(self) -> MissionRuntimeStatus:
        """
        Return current runtime status.
        """

        return MissionRuntimeStatus(state=self._state, mission_id=self._mission_id, scenario=self._scenario,
            started_at_utc=self._started_at_utc, stopped_at_utc=self._stopped_at_utc,
            events_processed=self._events_processed, log_path=self._log_path, last_error=self._last_error, )

    async def _run_loop(self, scenario: str, tick_interval_s: float, log_path: str, ) -> None:
        """
        Main live mission loop.

        This should reuse the same processing chain currently inside main.py.
        """

        mission_logger = MissionLogger()

        try:
            # TODO:
            # Move your existing main.py simulation setup here:
            #
            # wearable_simulator = DiverWearableSimulator(...)
            # preprocessor = SignalPreprocessor()
            # state_estimator = DiverStateEstimator()
            # alarm_engine = AlarmEngine()
            # link = AcousticLinkSimulator()
            # robot = RobotSystem()
            # report_builder = RobotReportBuilder(...)
            # surface_gateway = SurfaceGatewaySimulator()
            #
            # Then loop while not stopped.

            while not self._stop_event.is_set():
                # TODO:
                # Produce one simulation step here.
                #
                # mission_event = mission_logger.record_step(...)
                # self._backend.ingest_event(mission_event)
                # self._events_processed += 1

                await asyncio.sleep(tick_interval_s)

        except Exception as exc:
            self._last_error = str(exc)
            self._state = MissionRuntimeState.FAILED

            try:
                self._backend.abort_mission()
            except RuntimeError:
                pass

            raise

        finally:
            mission_logger.export_text_log(log_path)
