import type { UploadResponse } from "@/types";

type FindingsPanelProps = {
  result: UploadResponse;
};

function topValueOrFallback(
  entries: Array<{ value: string; count: number }>,
  fallback: string
): string {
  if (!entries.length) return fallback;
  return `${entries[0].value} (${entries[0].count})`;
}

export default function FindingsPanel({ result }: FindingsPanelProps) {
  const findings: string[] = [];
  const { summary } = result;

  findings.push(`Upload status: ${result.status.replaceAll("_", " ")}`);
  findings.push(
    `Blocked ratio: ${
      summary.total_events > 0
        ? Math.round((summary.blocked_events / summary.total_events) * 100)
        : 0
    }%`
  );
  findings.push(`Top category: ${topValueOrFallback(summary.top_categories, "N/A")}`);
  findings.push(`Top destination: ${topValueOrFallback(summary.top_destinations, "N/A")}`);
  findings.push(`Top source IP: ${topValueOrFallback(summary.top_source_ips, "N/A")}`);
  findings.push(`Anomalies detected: ${summary.total_anomalies}`);

  if (result.parse_errors_count > 0) {
    findings.push(`Parse errors present: ${result.parse_errors_count}`);
  }

  return (
    <aside className="analysis-section findings-panel">
      <div className="section-head">
        <h2>Findings Panel</h2>
        <span>High-level takeaways</span>
      </div>
      <ul className="findings-list">
        {findings.map((finding) => (
          <li key={finding}>{finding}</li>
        ))}
      </ul>
    </aside>
  );
}
