import { useEffect, useState } from "react";

import {
  fetchOperatorStatus,
  fetchRuntimeStatus,
  startRuntime,
  stopRuntime,
} from "./api/missionApi";
import "./App.css";
import { ApiErrorCard } from "./components/ApiErrorCard";
import { DashboardHeader } from "./components/DashboardHeader";
import { DiverStatusCard } from "./components/DiverStatusCard";
import { MissionControlPanel } from "./components/MissionControlPanel";
import { MissionOverview } from "./components/MissionOverview";
import type {
  MissionOperatorStatus,
  MissionRuntimeStatus,
} from "./types/mission";

function App() {
  const [runtimeStatus, setRuntimeStatus] =
    useState<MissionRuntimeStatus | null>(null);
  const [operatorStatus, setOperatorStatus] =
    useState<MissionOperatorStatus | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isBusy, setIsBusy] = useState(false);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function loadDashboardData() {
    try {
      setErrorMessage(null);

      const runtime = await fetchRuntimeStatus();
      setRuntimeStatus(runtime);

      if (runtime.state === "IDLE") {
        setOperatorStatus(null);
        setLastUpdatedAt(new Date());
        return;
      }

      try {
        const status = await fetchOperatorStatus();
        setOperatorStatus(status);
      } catch {
        setOperatorStatus(null);
      }

      setLastUpdatedAt(new Date());
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unknown dashboard error";

      setErrorMessage(message);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleStartMission(
    scenario: string,
    tickIntervalS: number,
  ) {
    try {
      setIsBusy(true);
      setErrorMessage(null);

      await startRuntime({
        scenario,
        tick_interval_s: tickIntervalS,
      });

      await loadDashboardData();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not start mission";

      setErrorMessage(message);
    } finally {
      setIsBusy(false);
    }
  }

  async function handleStopMission() {
    try {
      setIsBusy(true);
      setErrorMessage(null);

      await stopRuntime("Operator ended the mission.");

      await loadDashboardData();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not stop mission";

      setErrorMessage(message);
    } finally {
      setIsBusy(false);
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
        isRefreshing={isBusy}
        lastUpdatedAt={lastUpdatedAt}
        onRefresh={() => void loadDashboardData()}
      />

      {isLoading && <p className="info">Loading mission data...</p>}

      {errorMessage && <ApiErrorCard message={errorMessage} />}

      <div className="dashboard-stack">
        <MissionControlPanel
          runtimeStatus={runtimeStatus}
          isBusy={isBusy}
          onStartMission={handleStartMission}
          onStopMission={handleStopMission}
        />

        {operatorStatus && (
          <>
            <MissionOverview
              summary={{
                mission_id: operatorStatus.mission_id,
                scenario: operatorStatus.scenario,
                status: operatorStatus.status,
                events_received: operatorStatus.events_received,
                current_surface_mission_state:
                  operatorStatus.current_surface_mission_state,
                current_robot_mode:
                  operatorStatus.divers[0]?.robot_mode ?? null,
                emergency_event_count: operatorStatus.emergency_event_count,
                warning_event_count: operatorStatus.warning_event_count,
                stale_data_event_count: operatorStatus.stale_data_event_count,
              }}
            />

            <section className="diver-grid">
              {operatorStatus.divers.map((diver) => (
                <DiverStatusCard key={diver.diver_id} diver={diver} />
              ))}
            </section>
          </>
        )}
      </div>
    </main>
  );
}

export default App;