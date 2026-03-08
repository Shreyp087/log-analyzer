"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import AnalysisCharts from "@/components/AnalysisCharts";
import AnomaliesTable from "@/components/AnomaliesTable";
import ExecutiveSummaryPanel from "@/components/ExecutiveSummaryPanel";
import FindingsPanel from "@/components/FindingsPanel";
import SummaryCards from "@/components/SummaryCards";
import TimelineTable from "@/components/TimelineTable";
import { getAuthToken } from "@/lib/auth";
import type { UploadAnomalyPayload, UploadEventPreview, UploadResponse } from "@/types";

function storageKey(uploadId: string): string {
  return `analysis_result_${uploadId}`;
}

function readStoredAnalysis(uploadId: string): UploadResponse | null {
  if (typeof window === "undefined") return null;

  const raw = localStorage.getItem(storageKey(uploadId));
  if (!raw) return null;

  try {
    return JSON.parse(raw) as UploadResponse;
  } catch {
    return null;
  }
}

function eventLineNumber(event: UploadEventPreview, index: number): number {
  return event.lineNumber ?? index + 1;
}

function eventTimestampMs(event: UploadEventPreview): number | null {
  if (!event.event_time) return null;
  const parsed = new Date(event.event_time);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.getTime();
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

function toLocalDateTimeInputValue(timestampMs: number): string {
  const local = new Date(timestampMs - new Date().getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

export default function AnalysisPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [activeLines, setActiveLines] = useState<number[]>([]);
  const [rangeStart, setRangeStart] = useState("");
  const [rangeEnd, setRangeEnd] = useState("");
  const [actionFilter, setActionFilter] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState("ALL");

  const uploadId = useMemo(() => {
    const value = params?.id;
    if (Array.isArray(value)) return value[0] || "";
    return value || "";
  }, [params]);

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      router.replace("/");
      return;
    }

    if (!uploadId) {
      setError("Invalid analysis ID.");
      setLoading(false);
      return;
    }

    const cachedResult = readStoredAnalysis(uploadId);
    if (!cachedResult) {
      setError(
        "No stored analysis found for this upload ID in the current browser session. Re-upload the file to regenerate results."
      );
      setLoading(false);
      return;
    }

    setResult(cachedResult);
    setLoading(false);
  }, [router, uploadId]);

  useEffect(() => {
    if (!activeLines.length) return;
    const firstLine = activeLines[0];
    const row = document.getElementById(`event-row-${firstLine}`);
    if (row) {
      row.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [activeLines]);

  const onSelectLines = useCallback((lines: number[]) => {
    if (!lines.length) return;
    setActiveLines(lines);
  }, []);

  const onSelectLine = useCallback((lineNumber: number) => {
    setActiveLines([lineNumber]);
  }, []);

  const timeBounds = useMemo(() => {
    if (!result) {
      return { min: "", max: "" };
    }

    let minTs = Number.POSITIVE_INFINITY;
    let maxTs = Number.NEGATIVE_INFINITY;

    result.events_preview.forEach((event) => {
      const ts = eventTimestampMs(event);
      if (ts === null) return;
      if (ts < minTs) minTs = ts;
      if (ts > maxTs) maxTs = ts;
    });

    if (!Number.isFinite(minTs) || !Number.isFinite(maxTs)) {
      return { min: "", max: "" };
    }

    return {
      min: toLocalDateTimeInputValue(minTs),
      max: toLocalDateTimeInputValue(maxTs),
    };
  }, [result]);

  const filteredEvents = useMemo(() => {
    if (!result) return [];

    const rangeStartMs = rangeStart ? new Date(rangeStart).getTime() : null;
    const rangeEndMs = rangeEnd ? new Date(rangeEnd).getTime() : null;

    return result.events_preview.filter((event) => {
      const ts = eventTimestampMs(event);
      if (rangeStartMs !== null && ts !== null && ts < rangeStartMs) {
        return false;
      }
      if (rangeEndMs !== null && ts !== null && ts > rangeEndMs) {
        return false;
      }

      const normalizedAction = (event.action || "").toUpperCase();
      if (actionFilter === "ALL") return true;
      if (actionFilter === "ALLOW_OR_PERMIT") {
        return normalizedAction === "ALLOW" || normalizedAction === "PERMIT";
      }
      if (actionFilter === "OTHER") {
        return !["ALLOW", "PERMIT", "BLOCK"].includes(normalizedAction);
      }
      return normalizedAction === actionFilter;
    });
  }, [result, rangeStart, rangeEnd, actionFilter]);

  const filteredLineNumbers = useMemo(() => {
    const lineSet = new Set<number>();
    filteredEvents.forEach((event, index) => {
      lineSet.add(eventLineNumber(event, index));
    });
    return lineSet;
  }, [filteredEvents]);

  const filteredAnomalies = useMemo(() => {
    if (!result) return [];
    return result.anomalies.filter((anomaly) => {
      const severity = (anomaly.severity || "").toUpperCase();
      if (severityFilter !== "ALL" && severity !== severityFilter) {
        return false;
      }

      const lines = anomalyLines(anomaly);
      if (!lines.length) return true;
      return lines.some((line) => filteredLineNumbers.has(line));
    });
  }, [result, severityFilter, filteredLineNumbers]);

  const filteredStats = useMemo(() => {
    let allowOrPermit = 0;
    let blocked = 0;
    let other = 0;

    filteredEvents.forEach((event) => {
      const action = (event.action || "").toUpperCase();
      if (action === "ALLOW" || action === "PERMIT") {
        allowOrPermit += 1;
      } else if (action === "BLOCK") {
        blocked += 1;
      } else {
        other += 1;
      }
    });

    return {
      eventsInScope: filteredEvents.length,
      totalEvents: result?.events_preview.length || 0,
      allowOrPermit,
      blocked,
      other,
      anomalies: filteredAnomalies.length,
    };
  }, [filteredEvents, filteredAnomalies.length, result]);

  const resetRangeFilters = useCallback(() => {
    setRangeStart("");
    setRangeEnd("");
    setActionFilter("ALL");
    setSeverityFilter("ALL");
  }, []);

  if (loading) {
    return (
      <main className="shell">
        <section className="card">
          <p className="muted">Loading analysis...</p>
        </section>
      </main>
    );
  }

  if (!result) {
    return (
      <main className="shell">
        <section className="hero">
          <p className="chip">Analysis</p>
          <h1>Analysis Unavailable</h1>
          <p className="subtext">{error || "No analysis data available."}</p>
          <div className="hero-actions">
            <Link href="/upload" className="btn-secondary">
              Upload New File
            </Link>
            <Link href="/dashboard" className="btn-secondary">
              Back To Dashboard
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <section className="hero">
        <p className="chip">Analysis</p>
        <h1>Analysis #{result.upload_id}</h1>
        <p className="subtext">
          Uploaded file <code>{result.filename}</code> with status <code>{result.status}</code>.
        </p>
        <div className="hero-actions">
          <Link href="/upload" className="btn-secondary">
            Upload Another File
          </Link>
          <Link href="/dashboard" className="btn-secondary">
            Back To Dashboard
          </Link>
        </div>
      </section>

      <SummaryCards result={result} />
      <section className="analysis-section range-controls">
        <div className="section-head">
          <h2>Analysis Range</h2>
          <span>
            {filteredStats.eventsInScope} / {filteredStats.totalEvents} events in scope
          </span>
        </div>
        <div className="range-grid">
          <label className="field">
            <span>Start Time</span>
            <input
              type="datetime-local"
              className="input"
              value={rangeStart}
              min={timeBounds.min || undefined}
              max={timeBounds.max || undefined}
              onChange={(event) => setRangeStart(event.target.value)}
            />
          </label>
          <label className="field">
            <span>End Time</span>
            <input
              type="datetime-local"
              className="input"
              value={rangeEnd}
              min={timeBounds.min || undefined}
              max={timeBounds.max || undefined}
              onChange={(event) => setRangeEnd(event.target.value)}
            />
          </label>
          <label className="field">
            <span>Action Filter</span>
            <select
              className="input"
              value={actionFilter}
              onChange={(event) => setActionFilter(event.target.value)}
            >
              <option value="ALL">All Actions</option>
              <option value="ALLOW_OR_PERMIT">Allow + Permit</option>
              <option value="ALLOW">Allow Only</option>
              <option value="PERMIT">Permit Only</option>
              <option value="BLOCK">Block Only</option>
              <option value="OTHER">Other Actions</option>
            </select>
          </label>
          <label className="field">
            <span>Anomaly Severity</span>
            <select
              className="input"
              value={severityFilter}
              onChange={(event) => setSeverityFilter(event.target.value)}
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </label>
        </div>
        <div className="range-meta">
          <p className="muted">
            In-scope: {filteredStats.allowOrPermit} allow/permit, {filteredStats.blocked} blocked,{" "}
            {filteredStats.other} other, {filteredStats.anomalies} anomalies.
          </p>
          <button type="button" className="btn-secondary" onClick={resetRangeFilters}>
            Reset Filters
          </button>
        </div>
      </section>
      <ExecutiveSummaryPanel result={result} />
      <AnalysisCharts events={filteredEvents} summary={result.summary} />
      <TimelineTable
        events={filteredEvents}
        anomalies={filteredAnomalies}
        activeLines={activeLines}
        onSelectLine={onSelectLine}
      />
      <AnomaliesTable
        anomalies={filteredAnomalies}
        activeLines={activeLines}
        onSelectLines={onSelectLines}
      />
      <FindingsPanel result={result} />
    </main>
  );
}
