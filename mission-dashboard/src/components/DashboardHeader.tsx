import { formatDateTime } from "../utils/formatters";

type Props = {
  isRefreshing: boolean;
  lastUpdatedAt: Date | null;
  onRefresh: () => void;
};

export function DashboardHeader({
  isRefreshing,
  lastUpdatedAt,
  onRefresh,
}: Props) {
  return (
    <header className="hero">
      <div>
        <p className="eyebrow">Autonomous Diver Companion</p>
        <h1>Mission Operator Dashboard</h1>
        <p className="subtitle">
          Live mission state, robot decisions, communication events, and surface
          alerts.
        </p>

        <p className="last-updated">
          Last updated: {formatDateTime(lastUpdatedAt)}
        </p>
      </div>

      <button onClick={onRefresh} disabled={isRefreshing}>
        {isRefreshing ? "Refreshing..." : "Refresh"}
      </button>
    </header>
  );
}