import { useEffect, useState } from "react";

import { fetchMissionSummary, fetchRecentEvents } from "./api/missionApi";
import "./App.css";
import { ApiErrorCard } from "./components/ApiErrorCard";
import { DashboardHeader } from "./components/DashboardHeader";
import { MissionOverview } from "./components/MissionOverview";
import { RecentEventsTable } from "./components/RecentEventsTable";
import type { MissionEvent, MissionSummary } from "./types/mission";

function App() {
  const [summary, setSummary] = useState<MissionSummary | null>(null);
  const [events, setEvents] = useState<MissionEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function loadDashboardData() {
    try {
      setIsRefreshing(true);
      setErrorMessage(null);

      const [summaryResponse, recentEvents] = await Promise.all([
        fetchMissionSummary(),
        fetchRecentEvents(25),
      ]);

      setSummary(summaryResponse.summary);
      setEvents(recentEvents);
      setLastUpdatedAt(new Date());
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unknown dashboard error";

      setErrorMessage(message);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }

  useEffect(() => {
    void loadDashboardData();

    const intervalId = window.setInterval(() => {
      void loadDashboardData();
    }, 2000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, []);

  return (
    <main className="page">
      <DashboardHeader
        isRefreshing={isRefreshing}
        lastUpdatedAt={lastUpdatedAt}
        onRefresh={() => void loadDashboardData()}
      />

      {isLoading && <p className="info">Loading mission data...</p>}

      {errorMessage && <ApiErrorCard message={errorMessage} />}

      {summary && (
        <div className="dashboard-stack">
          <MissionOverview summary={summary} />
          <RecentEventsTable events={events} />
        </div>
      )}
    </main>
  );
}

export default App;