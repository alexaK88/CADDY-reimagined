"""
HTTP client for publishing mission simulation data to the FastAPI backend.

The simulation uses this client to:
- check that the API is reachable
- start a mission
- publish MissionEvent objects
- finish or abort a mission

This keeps main.py independent from the internal MissionBackend object.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from mission_logging.schemas import MissionEvent


class MissionApiClientError(RuntimeError):
    """
    Raised when the mission API cannot be reached or returns an error.
    """


@dataclass(frozen=True)
class MissionApiClientConfig:
    """
    Configuration for the mission API client.
    """

    base_url: str = "http://127.0.0.1:8000"
    timeout_s: float = 5.0


class MissionApiClient:
    """
    Small synchronous HTTP client for the mission FastAPI backend.
    """

    def __init__(self, config: MissionApiClientConfig | None = None):
        """
        Initialize the API client.
        """

        self.config = config or MissionApiClientConfig()
        self.base_url = self.config.base_url.rstrip("/")
        self._session = requests.Session()

    def health_check(self) -> dict[str, Any]:
        """
        Check whether the API is reachable.
        """

        return self._request(method="GET", path="/health", )

    def start_mission(self, scenario: str, mission_id: str | None = None, ) -> dict[str, Any]:
        """
        Start a mission through the API.
        """

        payload: dict[str, Any] = {
            "scenario": scenario,
            "mission_id": mission_id,
        }


        return self._request(method="POST", path="/missions/start", json=payload, )

    def publish_event(self, event: MissionEvent, ) -> dict[str, Any]:
        """
        Publish one MissionEvent to the API.
        """

        return self._request(method="POST", path="/missions/events", json=event.model_dump(mode="json"), )

    def finish_mission(self) -> dict[str, Any]:
        """
        Mark the active mission as completed through the API.
        """

        return self._request(method="POST", path="/missions/finish", )

    def abort_mission(self) -> dict[str, Any]:
        """
        Mark the active mission as aborted through the API.
        """

        return self._request(method="POST", path="/missions/abort", )

    def get_summary(self) -> dict[str, Any]:
        """
        Fetch the current compact mission summary.
        """

        return self._request(method="GET", path="/missions/summary", )

    def close(self) -> None:
        """
        Close the underlying HTTP session.
        """

        self._session.close()

    def _request(self, method: str, path: str, json: dict[str, Any] | None = None, ) -> dict[str, Any]:
        """
        Send one HTTP request and return the decoded JSON response.
        """

        url = f"{self.base_url}{path}"

        try:
            response = self._session.request(method=method, url=url, json=json, timeout=self.config.timeout_s, )
        except requests.RequestException as exc:
            raise MissionApiClientError(f"Mission API request failed: method={method}, url={url}, error={exc}") from exc

        if response.status_code >= 400:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text

            raise MissionApiClientError(f"Mission API returned error: "
                                        f"method={method}, url={url}, "
                                        f"status={response.status_code}, detail={detail}")

        try:
            return response.json()
        except ValueError as exc:
            raise MissionApiClientError(f"Mission API returned non-JSON response: method={method}, url={url}") from exc
