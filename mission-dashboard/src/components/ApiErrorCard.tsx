type Props = {
  message: string;
};

export function ApiErrorCard({ message }: Props) {
  return (
    <section className="card error-card">
      <p className="eyebrow">API connection</p>
      <h2>Dashboard cannot read mission data</h2>
      <p>{message}</p>
      <p className="muted">
        Start the FastAPI server first, then run the mission simulation.
      </p>
    </section>
  );
}