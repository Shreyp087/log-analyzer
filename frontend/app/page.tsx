const stageItems = [
  { stage: "Stage 1", status: "Done", label: "Project foundation" },
  { stage: "Stage 2", status: "Done", label: "Backend shell" },
  { stage: "Stage 3", status: "Done", label: "Data model + migrations" },
  { stage: "Stage 4", status: "Done", label: "Health + auth API" },
  { stage: "Stage 5", status: "Done", label: "Parsing layer" },
  { stage: "Stage 6", status: "Done", label: "Upload + summary flow" },
  { stage: "Stage 7", status: "Done", label: "Anomaly detection" },
  { stage: "Stage 8", status: "Done", label: "Frontend shell" },
  { stage: "Stage 9", status: "Pending", label: "API/frontend integration" }
];

const backendContracts = [
  "GET /health",
  "POST /auth/register",
  "POST /auth/login",
  "GET /auth/me",
  "POST /uploads"
];

export default function HomePage() {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  return (
    <main className="shell">
      <section className="hero">
        <p className="chip">Cyber Ops UI Shell</p>
        <h1>Log Analyzer Frontend</h1>
        <p className="subtext">
          Frontend foundation built after backend contract stabilization. Current shell tracks
          pipeline status and API contract readiness.
        </p>
      </section>

      <section className="grid">
        <article className="card">
          <h2>Backend Contract</h2>
          <p className="muted">Base URL: {apiBase}</p>
          <ul className="list">
            {backendContracts.map((route) => (
              <li key={route}>
                <code>{route}</code>
              </li>
            ))}
          </ul>
        </article>

        <article className="card">
          <h2>Build Progress</h2>
          <ul className="list">
            {stageItems.map((item) => (
              <li key={item.stage} className="stage-row">
                <span>{item.stage}</span>
                <span className={item.status === "Done" ? "done" : "pending"}>{item.status}</span>
                <small>{item.label}</small>
              </li>
            ))}
          </ul>
        </article>
      </section>
    </main>
  );
}
