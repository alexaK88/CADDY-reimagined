type Props = {
  value: string | null | undefined;
};

export function StatusBadge({ value }: Props) {
  const displayValue = value ?? "UNKNOWN";

  return (
    <span className={`status-badge status-badge-${displayValue.toLowerCase()}`}>
      {displayValue.replaceAll("_", " ")}
    </span>
  );
}