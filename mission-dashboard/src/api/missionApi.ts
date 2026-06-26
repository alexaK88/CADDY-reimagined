import { API_BASE_URL } from "../config/appConfig";
import type {
  MissionEvent,
  MissionSummaryResponse,
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

export async function fetchMissionSummary(): Promise<MissionSummaryResponse> {
  return requestJson<MissionSummaryResponse>("/missions/summary");
}

export async function fetchRecentEvents(limit = 25): Promise<MissionEvent[]> {
  return requestJson<MissionEvent[]>(`/missions/events/recent?limit=${limit}`);
}