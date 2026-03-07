import { RISK_LEVELS, type RiskLevel } from "@/lib/constants";
import type { UploadResponse } from "@/types";

type ExecutiveSummaryPanelProps = {
  result: UploadResponse;
};

function asPercent(numerator: number, denominator: number): number {
  if (denominator <= 0) return 0;
  return Math.round((numerator / denominator) * 100);
}

function normalizeRiskLevel(value: string | undefined): RiskLevel {
  const normalized = (value || "").toUpperCase();
  return RISK_LEVELS.includes(normalized as RiskLevel)
    ? (normalized as RiskLevel)
    : "LOW";
}

function riskClass(level: RiskLevel): string {
  if (level === "CRITICAL") return "risk-chip risk-critical";
  if (level === "HIGH") return "risk-chip risk-high";
  if (level === "MEDIUM") return "risk-chip risk-medium";
  return "risk-chip risk-low";
}

export default function ExecutiveSummaryPanel({ result }: ExecutiveSummaryPanelProps) {
  const summary = result.ai_summary;
  const blockRate = asPercent(result.summary.blocked_events, result.summary.total_events);

  if (!summary) {
    return (
      <section className="analysis-section executive-summary-panel">
        <div className="section-head">
          <h2>Executive Summary</h2>
          <span className="muted">Unavailable</span>
        </div>
        <p className="muted">
          No AI executive summary is attached to this upload result. Re-upload to regenerate.
        </p>
      </section>
    );
  }

  const riskLevel = normalizeRiskLevel(summary.riskLevel);

  return (
    <section className="analysis-section executive-summary-panel">
      <div className="section-head">
        <h2>Executive Summary</h2>
        <span className={riskClass(riskLevel)}>{riskLevel}</span>
      </div>

      <p className="executive-summary-text">{summary.executiveSummary}</p>

      <div className="executive-stat-grid">
        <article className="executive-stat">
          <h3>Total Events</h3>
          <p>{result.summary.total_events}</p>
        </article>
        <article className="executive-stat">
          <h3>Blocked Events</h3>
          <p>
            {result.summary.blocked_events} ({blockRate}%)
          </p>
        </article>
        <article className="executive-stat">
          <h3>Anomalies</h3>
          <p>{result.anomalies.length}</p>
        </article>
      </div>

      <div className="executive-list-grid">
        <div>
          <h3>Key Findings</h3>
          <ul className="findings-list">
            {summary.keyFindings.slice(0, 3).map((finding) => (
              <li key={finding}>{finding}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3>Recommendations</h3>
          <ul className="findings-list">
            {summary.recommendations.slice(0, 2).map((recommendation) => (
              <li key={recommendation}>{recommendation}</li>
            ))}
          </ul>
        </div>
      </div>

      {summary.immediateActions.length > 0 ? (
        <div className="executive-immediate">
          <h3>Immediate Actions</h3>
          <ul className="findings-list">
            {summary.immediateActions.slice(0, 2).map((action) => (
              <li key={action}>{action}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
