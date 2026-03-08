"use client";

import { Fragment, useState } from "react";
import type { UploadAnomalyPayload } from "@/types";

type AnomaliesTableProps = {
  anomalies: UploadAnomalyPayload[];
  activeLines?: number[];
  onSelectLines?: (lines: number[]) => void;
};

function severityClass(severity: string): string {
  const normalized = severity.toLowerCase();
  if (normalized === "critical") return "sev-critical";
  if (normalized === "high") return "sev-high";
  if (normalized === "medium") return "sev-medium";
  return "sev-low";
}

function anomalyLines(anomaly: UploadAnomalyPayload): number[] {
  if (Array.isArray(anomaly.affectedLines) && anomaly.affectedLines.length > 0) {
    return anomaly.affectedLines;
  }
  if (typeof anomaly.event_row === "number") {
    return [anomaly.event_row];
  }
  return [];
}

function anomalyType(anomaly: UploadAnomalyPayload): string {
  return anomaly.type || anomaly.anomaly_type || "unknown_anomaly";
}

function anomalyText(anomaly: UploadAnomalyPayload): string {
  return anomaly.explanation || anomaly.description || "No explanation";
}

export default function AnomaliesTable({
  anomalies,
  activeLines = [],
  onSelectLines
}: AnomaliesTableProps) {
  const activeSet = new Set(activeLines);
  const [expandedRows, setExpandedRows] = useState<Record<number, boolean>>({});

  const toggleExpanded = (index: number) => {
    setExpandedRows((prev) => ({ ...prev, [index]: !prev[index] }));
  };

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
                <th>Event Rows</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Confidence</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {anomalies.map((anomaly, index) => {
                const lines = anomalyLines(anomaly);
                const linesLabel = lines.length > 0 ? lines.join(", ") : "-";
                const isLinked = lines.some((line) => activeSet.has(line));
                const description = anomalyText(anomaly);
                const isExpanded = Boolean(expandedRows[index]);
                const hasEnrichment = Boolean(anomaly.aiEnrichment);
                return (
                  <Fragment key={`${anomalyType(anomaly)}-${index}`}>
                    <tr
                      className={isLinked ? "anomaly-row-active" : ""}
                      onClick={() => {
                        onSelectLines?.(lines);
                        if (hasEnrichment) {
                          toggleExpanded(index);
                        }
                      }}
                    >
                      <td>{linesLabel}</td>
                      <td>
                        <div className="anomaly-type-cell">
                          <span>{anomalyType(anomaly)}</span>
                          {hasEnrichment ? <span className="ai-enriched-badge">AI ENRICHED</span> : null}
                        </div>
                      </td>
                      <td>
                        <span className={`sev-chip ${severityClass(anomaly.severity)}`}>
                          {anomaly.severity}
                        </span>
                      </td>
                      <td>{Math.round(anomaly.confidence * 100)}%</td>
                      <td className="anomaly-description-cell">
                        <span className="anomaly-description-text">{description}</span>
                        {hasEnrichment ? (
                          <button
                            type="button"
                            className="anomaly-expand-btn"
                            onClick={(event) => {
                              event.stopPropagation();
                              toggleExpanded(index);
                            }}
                          >
                            {isExpanded ? "▲ less" : "▼ more"}
                          </button>
                        ) : null}
                      </td>
                    </tr>
                    {hasEnrichment && isExpanded ? (
                      <tr className="anomaly-enrichment-row">
                        <td colSpan={5}>
                          <div className="anomaly-enrichment-block">
                            <p>
                              <strong>MITRE:</strong> {anomaly.aiEnrichment?.mitreId} -{" "}
                              {anomaly.aiEnrichment?.mitreName}
                            </p>
                            <p>
                              <strong>Attack Pattern:</strong> {anomaly.aiEnrichment?.attackPattern}
                            </p>
                            <p>
                              <strong>Containment:</strong> {anomaly.aiEnrichment?.containmentStep}
                            </p>
                          </div>
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
