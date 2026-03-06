import type { UploadAnomalyPayload } from "@/types";

type AnomaliesTableProps = {
  anomalies: UploadAnomalyPayload[];
};

function severityClass(severity: string): string {
  const normalized = severity.toLowerCase();
  if (normalized === "high") return "sev-high";
  if (normalized === "medium") return "sev-medium";
  return "sev-low";
}

export default function AnomaliesTable({ anomalies }: AnomaliesTableProps) {
  return (
    <section className="analysis-section">
      <div className="section-head">
        <h2>Anomalies</h2>
        <span>{anomalies.length} findings</span>
      </div>

      {anomalies.length === 0 ? (
        <p className="muted">No anomalies detected for this upload.</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Event ID</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Confidence</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {anomalies.map((anomaly, index) => (
                <tr key={`${anomaly.event_id}-${anomaly.anomaly_type}-${index}`}>
                  <td>{anomaly.event_id}</td>
                  <td>{anomaly.anomaly_type}</td>
                  <td>
                    <span className={`sev-chip ${severityClass(anomaly.severity)}`}>
                      {anomaly.severity}
                    </span>
                  </td>
                  <td>{Math.round(anomaly.confidence * 100)}%</td>
                  <td className="truncate">{anomaly.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
