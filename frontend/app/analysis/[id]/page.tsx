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
import type { UploadResponse } from "@/types";

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

export default function AnalysisPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [activeLines, setActiveLines] = useState<number[]>([]);

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
      <ExecutiveSummaryPanel result={result} />
      <AnalysisCharts events={result.events_preview} summary={result.summary} />
      <TimelineTable
        events={result.events_preview}
        anomalies={result.anomalies}
        activeLines={activeLines}
        onSelectLine={onSelectLine}
      />
      <AnomaliesTable
        anomalies={result.anomalies}
        activeLines={activeLines}
        onSelectLines={onSelectLines}
      />
      <FindingsPanel result={result} />
    </main>
  );
}
