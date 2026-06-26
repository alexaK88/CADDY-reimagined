import type { MissionSummary } from "../types/mission";
import { prettifyEnum } from "../utils/formatters";
import { MetricCard } from "./MetricCard";
import { StatusBadge } from "./StatusBadge";

type Props = {
  summary: MissionSummary;
};

export function MissionOverview({ summary }: Props) {
  return (
    <section className="card mission-overview">
      <div className="card-header">
        <div>
          <p className="eyebrow">Mission overview</p>
          <h2>{summary.mission_id}</h2>
        </div>

        <StatusBadge value={summary.status} />
      </div>

      <div className="overview-grid">
        <div className="overview-item">
          <span>Scenario</span>
          <strong>{prettifyEnum(summary.scenario)}</strong>
        </div>

        <div className="overview-item">
          <span>Robot mode</span>
          <strong>{prettifyEnum(summary.current_robot_mode)}</strong>
        </div>

        <div className="overview-item">
          <span>Surface state</span>
          <StatusBadge value={summary.current_surface_mission_state} />
        </div>

        <div className="overview-item">
          <span>Events received</span>
          <strong>{summary.events_received}</strong>
        </div>
      </div>

      <div className="metric-grid">
        <MetricCard
          label="Emergencies"
          value={summary.emergency_event_count}
          hint="Surface emergency events"
        />

        <MetricCard
          label="Warnings"
          value={summary.warning_event_count}
          hint="Attention-required events"
        />

        <MetricCard
          label="Stale data"
          value={summary.stale_data_event_count}
          hint="Diver data stale events"
        />
      </div>
    </section>
  );
}