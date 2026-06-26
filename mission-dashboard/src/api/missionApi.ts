import { API_BASE_URL } from "../config/appConfig";
import type {
  MissionEvent,
  MissionOperatorStatus,
  MissionRuntimeStatus,
  MissionSummaryResponse,
  StartRuntimeRequest,
} from "../types/mission";

async function requestJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);

  if (!response.ok) {
    const detail = await response.text();

    throw new Error(
      `API request failed: ${response.status} ${response.statusText} ${detail}`,
    );
  }

  return response.json() as Promise<T>;
}

async function postJson<TResponse, TPayload>(
  path: string,
  payload?: TPayload,
): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: payload === undefined ? undefined : JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.text();

    throw new Error(
      `API request failed: ${response.status} ${response.statusText} ${detail}`,
    );
  }

  return response.json() as Promise<TResponse>;
}

export async function fetchMissionSummary(): Promise<MissionSummaryResponse> {
  return requestJson<MissionSummaryResponse>("/missions/summary");
}

export async function fetchRecentEvents(limit = 25): Promise<MissionEvent[]> {
  return requestJson<MissionEvent[]>(`/missions/events/recent?limit=${limit}`);
}

export async function fetchRuntimeStatus(): Promise<MissionRuntimeStatus> {
  return requestJson<MissionRuntimeStatus>("/runtime/status");
}

export async function startRuntime(
  payload: StartRuntimeRequest,
): Promise<MissionRuntimeStatus> {
  return postJson<MissionRuntimeStatus, StartRuntimeRequest>(
    "/runtime/start",
    payload,
  );
}

export async function stopRuntime(
  reason = "Operator ended the mission.",
): Promise<MissionRuntimeStatus> {
  return postJson<MissionRuntimeStatus, { reason: any }>("/runtime/stop", {
    reason,
  });
}

export async function fetchOperatorStatus(): Promise<MissionOperatorStatus> {
  return requestJson<MissionOperatorStatus>("/missions/operator-status");
}