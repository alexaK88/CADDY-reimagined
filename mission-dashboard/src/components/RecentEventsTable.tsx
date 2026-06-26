import type { MissionEvent } from "../types/mission";
import {
  formatElapsedTime,
  formatList,
  formatNullable,
  prettifyEnum,
} from "../utils/formatters";
import { StatusBadge } from "./StatusBadge";

type Props = {
  events: MissionEvent[];
};

export function RecentEventsTable({ events }: Props) {
  return (
    <section className="card">
      <div className="card-header">
        <div>
          <p className="eyebrow">Recent mission events</p>
          <h2>Timeline</h2>
        </div>

        <span className="muted">{events.length} events shown</span>
      </div>

      {events.length === 0 ? (
        <p className="muted">No mission events received yet.</p>
      ) : (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Wearable</th>
                <th>Alarms</th>
                <th>RX</th>
                <th>Robot</th>
                <th>Surface</th>
                <th>Reason</th>
              </tr>
            </thead>

            <tbody>
              {events.map((event) => (
                <tr key={`${event.scenario}-${event.event_index}`}>
                  <td>{formatElapsedTime(event.elapsed_time_s)}</td>

                  <td>
                    <StatusBadge value={event.wearable_safety_state} />
                  </td>

                  <td>{formatList(event.wearable_alarm_codes)}</td>

                  <td>
                    {formatNullable(event.communication_receive_status)}
                    {event.communication_rx_sequence_number !== null &&
                      event.communication_rx_sequence_number !== undefined && (
                        <span className="muted">
                          {" "}
                          #{event.communication_rx_sequence_number}
                        </span>
                      )}
                  </td>

                  <td>{prettifyEnum(event.robot_mode)}</td>

                  <td>
                    <StatusBadge value={event.surface_mission_state} />
                  </td>

                  <td className="reason-cell">{event.robot_reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}