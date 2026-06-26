import type { DiverOperatorStatus } from "../types/mission";
import {
  formatElapsedTime,
  formatList,
  formatNullable,
  prettifyEnum,
} from "../utils/formatters";
import { StatusBadge } from "./StatusBadge";

type Props = {
  diver: DiverOperatorStatus;
};

export function DiverStatusCard({ diver }: Props) {
  return (
    <article className="card diver-card">
      <div className="card-header">
        <div>
          <p className="eyebrow">Diver status</p>
          <h2>{diver.diver_id}</h2>
        </div>

        <StatusBadge value={diver.surface_mission_state} />
      </div>

      <div className="diver-status-grid">
        <div>
          <span>Wearable state</span>
          <StatusBadge value={diver.wearable_safety_state} />
        </div>

        <div>
          <span>Robot received</span>
          <StatusBadge value={diver.received_safety_state} />
        </div>

        <div>
          <span>Robot mode</span>
          <strong>{prettifyEnum(diver.robot_mode)}</strong>
        </div>

        <div>
          <span>Data freshness</span>
          <strong>{diver.diver_data_stale ? "STALE" : "FRESH"}</strong>
        </div>
      </div>

      <div className="diver-details">
        <p>
          <span>Active alarms:</span>{" "}
          <strong>{formatList(diver.active_alarm_codes)}</strong>
        </p>

        <p>
          <span>Surface alerts:</span>{" "}
          <strong>{formatList(diver.active_surface_alert_codes)}</strong>
        </p>

        <p>
          <span>Latest event time:</span>{" "}
          <strong>
            {diver.latest_event_time_s === null
              ? "-"
              : formatElapsedTime(diver.latest_event_time_s)}
          </strong>
        </p>

        <p>
          <span>Packet age:</span>{" "}
          <strong>
            {diver.latest_packet_age_s === null
              ? "-"
              : formatElapsedTime(diver.latest_packet_age_s)}
          </strong>
        </p>

        <p>
          <span>Notify surface:</span>{" "}
          <strong>{formatNullable(String(diver.robot_notify_surface))}</strong>
        </p>
      </div>
    </article>
  );
}