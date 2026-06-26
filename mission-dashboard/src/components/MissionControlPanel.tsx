import { useState } from "react";

import type { MissionRuntimeStatus } from "../types/mission";
import { prettifyEnum } from "../utils/formatters";
import { StatusBadge } from "./StatusBadge";

type Props = {
  runtimeStatus: MissionRuntimeStatus | null;
  isBusy: boolean;
  onStartMission: (scenario: string, tickIntervalS: number) => void;
  onStopMission: () => void;
};

export function MissionControlPanel({
  runtimeStatus,
  isBusy,
  onStartMission,
  onStopMission,
}: Props) {
  const [scenario, setScenario] = useState("normal");
  const [tickIntervalS, setTickIntervalS] = useState(1);

  const runtimeState = runtimeStatus?.state ?? "IDLE";
  const isRunning = runtimeState === "RUNNING" || runtimeState === "STOPPING";

  return (
    <section className="card control-panel">
      <div className="card-header">
        <div>
          <p className="eyebrow">Mission control</p>
          <h2>Runtime</h2>
        </div>

        <StatusBadge value={runtimeState} />
      </div>

      <div className="control-grid">
        <label>
          <span>Scenario</span>
          <select
            value={scenario}
            onChange={(event) => setScenario(event.target.value)}
            disabled={isRunning || isBusy}
          >
            <option value="normal">Normal</option>
            <option value="fast_ascent">Fast ascent</option>
            <option value="emergency_button">Emergency button</option>
            <option value="low_gas">Low gas</option>
            <option value="no_motion">No motion</option>
            <option value="weak_link">Weak link</option>
            <option value="lost_link">Lost link</option>
            <option value="battery_low">Battery low</option>
          </select>
        </label>

        <label>
          <span>Tick interval [s]</span>
          <input
            type="number"
            min="0.2"
            step="0.1"
            value={tickIntervalS}
            onChange={(event) => setTickIntervalS(Number(event.target.value))}
            disabled={isRunning || isBusy}
          />
        </label>
      </div>

      <div className="button-row">
        {!isRunning ? (
          <button
            onClick={() => onStartMission(scenario, tickIntervalS)}
            disabled={isBusy}
          >
            {isBusy ? "Starting..." : "Start mission"}
          </button>
        ) : (
          <button
            className="danger-button"
            onClick={onStopMission}
            disabled={isBusy || runtimeState === "STOPPING"}
          >
            {runtimeState === "STOPPING" ? "Stopping..." : "End mission"}
          </button>
        )}
      </div>

      <div className="runtime-details">
        <p>
          <span>Mission:</span>{" "}
          <strong>{runtimeStatus?.mission_id ?? "-"}</strong>
        </p>
        <p>
          <span>Scenario:</span>{" "}
          <strong>{prettifyEnum(runtimeStatus?.scenario)}</strong>
        </p>
        <p>
          <span>Events processed:</span>{" "}
          <strong>{runtimeStatus?.events_processed ?? 0}</strong>
        </p>
        <p>
          <span>Log:</span>{" "}
          <strong>{runtimeStatus?.log_path ?? "-"}</strong>
        </p>
      </div>

      {runtimeStatus?.last_error && (
        <p className="runtime-error">{runtimeStatus.last_error}</p>
      )}
    </section>
  );
}