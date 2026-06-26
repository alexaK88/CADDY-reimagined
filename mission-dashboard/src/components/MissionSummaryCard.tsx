import type { MissionSummary } from "../types/mission";

type Props = {
  summary: MissionSummary;
};

export function MissionSummaryCard({ summary }: Props) {
  return (
    <section className="card">
      <div className="card-header">
        <div>
          <p className="eyebrow">Mission</p>
          <h2>{summary.mission_id}</h2>
        </div>

        <span className={`status-pill status-${summary.status.toLowerCase()}`}>
          {summary.status}
        </span>
      </div>

      <div className="grid">
        <div>
          <span className="label">Scenario</span>
          <strong>{summary.scenario}</strong>
        </div>

        <div>
          <span className="label">Events</span>
          <strong>{summary.events_received}</strong>
        </div>

        <div>
          <span className="label">Robot mode</span>
          <strong>{summary.current_robot_mode ?? "-"}</strong>
        </div>

        <div>
          <span className="label">Surface state</span>
          <strong>{summary.current_surface_mission_state ?? "-"}</strong>
        </div>
      </div>
    </section>
  );
}