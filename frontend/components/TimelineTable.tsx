"use client";

import { useMemo, useState } from "react";

import { SEVERITY_RANK } from "@/lib/constants";
import type { UploadAnomalyPayload, UploadEventPreview } from "@/types";

type TimelineTableProps = {
  events: UploadEventPreview[];
  anomalies: UploadAnomalyPayload[];
  activeLines?: number[];
  onSelectLine?: (lineNumber: number) => void;
};

type TimelineEntry = {
  lineNumber: number;
  eventTime: string | null;
  user: string | null;
  sourceIp: string | null;
  action: string | null;
  category: string | null;
  url: string | null;
  bytes: number | null;
  raw: string | null;
  threat: string | null;
  severity: string | null;
  isAnomalous: boolean;
  anomalies: UploadAnomalyPayload[];
};

function formatTime(value: string | null): string {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

function formatBytes(value: number | null): string {
  if (value === null || Number.isNaN(value)) return "-";
  if (value >= 1024 * 1024 * 1024) return `${(value / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  if (value >= 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  if (value >= 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${value} B`;
}

function hasThreat(threat: string | null | undefined): boolean {
  if (!threat) return false;
  return threat.trim().toLowerCase() !== "none";
}

function normalizeType(value: string): string {
  return value
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function shortenAnomalyType(value: string): string {
  const normalized = normalizeType(value);
  if (!normalized) return "ANOMALY";
  return normalized
    .replace(/_REQUESTS?$/, "")
    .replace(/_EVENTS?$/, "")
    .replace(/_DETECTIONS?$/, "");
}

function severityRank(value: string | null | undefined): number {
  return SEVERITY_RANK[(value || "").toLowerCase()] || 0;
}

function rowState(entry: TimelineEntry): string {
  const highestSeverity = entry.anomalies.reduce((best, anomaly) => {
    const rank = severityRank(anomaly.severity);
    return rank > best ? rank : best;
  }, 0);
  const entrySeverity = severityRank(entry.severity);
  const combinedSeverity = Math.max(highestSeverity, entrySeverity);

  if (combinedSeverity >= 4) return "row-state-critical";
  if (combinedSeverity >= 3) return "row-state-high";
  if (hasThreat(entry.threat)) return "row-state-threat";
  if (entry.isAnomalous) {
    if (combinedSeverity >= 2) return "row-state-medium";
    if (combinedSeverity >= 1) return "row-state-low";
    return "row-state-anomalous";
  }
  return "";
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

export default function TimelineTable({
  events,
  anomalies,
  activeLines = [],
  onSelectLine
}: TimelineTableProps) {
  const [anomaliesOnly, setAnomaliesOnly] = useState(false);

  const entries = useMemo<TimelineEntry[]>(() => {
    const anomaliesByLine = new Map<number, UploadAnomalyPayload[]>();

    for (const anomaly of anomalies) {
      for (const line of anomalyLines(anomaly)) {
        const bucket = anomaliesByLine.get(line) || [];
        bucket.push(anomaly);
        anomaliesByLine.set(line, bucket);
      }
    }

    return events.map((event, index) => {
      const lineNumber = event.lineNumber ?? index + 1;
      const rowAnomalies = anomaliesByLine.get(lineNumber) || event.anomalies || [];
      const inferredSeverity = rowAnomalies[0]?.severity || null;
      const inferredAnomalous = rowAnomalies.length > 0;

      return {
        lineNumber,
        eventTime: event.event_time ?? null,
        user: event.user ?? event.username ?? null,
        sourceIp: event.sourceIp ?? event.source_ip ?? null,
        action: event.action ?? null,
        category: event.category ?? null,
        url: event.url ?? event.destination ?? null,
        bytes: event.bytes_transferred ?? null,
        raw: event.raw ?? null,
        threat: event.threat ?? "None",
        severity: event.severity ?? inferredSeverity,
        isAnomalous: event.isAnomalous ?? inferredAnomalous,
        anomalies: rowAnomalies
      };
    });
  }, [events, anomalies]);

  const filteredEntries = useMemo(() => {
    if (!anomaliesOnly) return entries;
    return entries.filter((entry) => entry.isAnomalous || hasThreat(entry.threat));
  }, [entries, anomaliesOnly]);

  const activeLineSet = useMemo(() => new Set(activeLines), [activeLines]);

  return (
    <section className="analysis-section">
      <div className="section-head">
        <h2>Event Timeline</h2>
        <span>{filteredEntries.length} rows</span>
      </div>

      <div className="table-controls">
        <button
          type="button"
          className={`filter-toggle ${anomaliesOnly ? "active" : ""}`}
          onClick={() => setAnomaliesOnly((prev) => !prev)}
        >
          ANOMALIES ONLY
        </button>
      </div>

      {filteredEntries.length === 0 ? (
        <p className="muted">No event rows match the current filter.</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Line</th>
                <th>Time</th>
                <th>User</th>
                <th>Source IP</th>
                <th>Action</th>
                <th>Category</th>
                <th>Destination</th>
                <th>Bytes</th>
                <th>Flags</th>
              </tr>
            </thead>
            <tbody>
              {filteredEntries.map((entry) => {
                const stateClass = rowState(entry);

                return (
                  <tr
                    id={`event-row-${entry.lineNumber}`}
                    key={`line-${entry.lineNumber}`}
                    className={`timeline-row ${stateClass} ${
                      activeLineSet.has(entry.lineNumber) ? "timeline-row-active" : ""
                    }`}
                    onClick={() => onSelectLine?.(entry.lineNumber)}
                  >
                    <td>{entry.lineNumber}</td>
                    <td>{formatTime(entry.eventTime)}</td>
                    <td>{entry.user || "-"}</td>
                    <td>{entry.sourceIp || "-"}</td>
                    <td>{entry.action || "-"}</td>
                    <td>{entry.category || "-"}</td>
                    <td className="truncate" title={entry.raw || undefined}>
                      {entry.url || "-"}
                    </td>
                    <td>{formatBytes(entry.bytes)}</td>
                    <td>
                      <div className="row-badges">
                        {hasThreat(entry.threat) ? (
                          <span className="row-badge threat-badge">🚨 THREAT</span>
                        ) : null}
                        {entry.anomalies.map((anomaly, anomalyIndex) => {
                          const anomalyType =
                            anomaly.type || anomaly.anomaly_type || "anomaly_detected";
                          const anomalyExplanation =
                            anomaly.explanation ||
                            anomaly.description ||
                            "Anomaly flagged on this entry.";
                          return (
                            <span
                              key={`${entry.lineNumber}-${anomalyIndex}-${anomalyType}`}
                              className="row-badge anomaly-badge"
                              title={anomalyExplanation}
                            >
                              {shortenAnomalyType(anomalyType)}
                            </span>
                          );
                        })}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
