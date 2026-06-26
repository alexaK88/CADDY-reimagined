import type { MissionSummary } from "../types/mission";

type Props = {
  summary: MissionSummary;
};

export function MissionStatusPanel({ summary }: Props) {
  return (
    <section className="card">
      <p className="eyebrow">Mission counters</p>

      <div className="counter-grid">
        <div className="counter">
          <span>Emergencies</span>
          <strong>{summary.emergency_event_count}</strong>
        </div>

        <div className="counter">
          <span>Warnings</span>
          <strong>{summary.warning_event_count}</strong>
        </div>

        <div className="counter">
          <span>Stale data</span>
          <strong>{summary.stale_data_event_count}</strong>
        </div>
      </div>
    </section>
  );
}