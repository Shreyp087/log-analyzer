"use client";

import Link from "next/link";
import { DragEvent, useMemo, useState } from "react";

import { analyzeUpload, ApiRequestError, uploadLogFile } from "@/lib/api";
import type { UploadResponse } from "@/types";

type UploadDropzoneProps = {
  onUploaded?: (payload: UploadResponse) => void;
};

const ALLOWED_EXTENSIONS = [".log", ".txt", ".csv"] as const;
const MAX_UPLOAD_BYTES = 20 * 1024 * 1024;

function formatBytes(value: number): string {
  if (value >= 1024 * 1024) {
    return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  }
  if (value >= 1024) {
    return `${Math.ceil(value / 1024)} KB`;
  }
  return `${value} B`;
}

function hasAllowedExtension(fileName: string): boolean {
  const normalized = fileName.toLowerCase();
  return ALLOWED_EXTENSIONS.some((extension) => normalized.endsWith(extension));
}

function validateFile(candidate: File): string | null {
  if (!hasAllowedExtension(candidate.name)) {
    return "Invalid file type. Allowed extensions: .log, .txt, .csv";
  }
  if (candidate.size > MAX_UPLOAD_BYTES) {
    return `File is too large. Maximum size is ${formatBytes(MAX_UPLOAD_BYTES)}.`;
  }
  return null;
}

type UploadPhase = "idle" | "uploading" | "analyzing";

export default function UploadDropzone({ onUploaded }: UploadDropzoneProps) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<UploadPhase>("idle");
  const [error, setError] = useState<string>("");
  const [result, setResult] = useState<UploadResponse | null>(null);

  const selectedFileLabel = useMemo(() => {
    if (!file) return "No file selected";
    return `${file.name} (${formatBytes(file.size)})`;
  }, [file]);

  const uploading = phase !== "idle";

  const setValidatedFile = (candidate: File | null) => {
    if (!candidate) return;
    const validationError = validateFile(candidate);
    if (validationError) {
      setFile(null);
      setResult(null);
      setError(validationError);
      return;
    }
    setFile(candidate);
    setResult(null);
    setError("");
  };

  const onDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);
    setValidatedFile(event.dataTransfer.files?.[0] || null);
  };

  const onDragOver = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(true);
  };

  const onDragLeave = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);
  };

  const submitUpload = async () => {
    if (!file) {
      setError("Please select a valid log file before uploading.");
      return;
    }

    setPhase("uploading");
    setError("");

    try {
      const upload = await uploadLogFile(file, "zscaler");
      setPhase("analyzing");

      const payload = await analyzeUpload(upload.upload_id);
      if (typeof window !== "undefined") {
        localStorage.setItem(`analysis_result_${payload.upload_id}`, JSON.stringify(payload));
      }
      setResult(payload);
      onUploaded?.(payload);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.message);
      } else {
        setError("Upload failed. Please retry.");
      }
    } finally {
      setPhase("idle");
    }
  };

  return (
    <section className="upload-card">
      <label
        className={`dropzone ${dragActive ? "active" : ""}`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
      >
        <input
          type="file"
          accept=".log,.txt,.csv"
          onChange={(event) => setValidatedFile(event.target.files?.[0] || null)}
        />
        <strong>Drop Zscaler log file here</strong>
        <span>or click to browse</span>
      </label>

      <p className="muted">{selectedFileLabel}</p>
      <p className="muted">
        Accepted files: <code>.log</code>, <code>.txt</code>, <code>.csv</code>. Max size:{" "}
        {formatBytes(MAX_UPLOAD_BYTES)}.
      </p>

      <button type="button" className="btn-primary" onClick={submitUpload} disabled={uploading}>
        {phase === "uploading"
          ? "Uploading..."
          : phase === "analyzing"
            ? "Analyzing..."
            : "Upload And Analyze"}
      </button>

      {error ? <p className="form-feedback error">{error}</p> : null}

      {result ? (
        <div className="upload-result">
          <h3>Upload Result</h3>
          <ul className="list">
            <li>
              <code>upload_id</code>: {result.upload_id}
            </li>
            <li>
              <code>events_saved</code>: {result.events_saved}
            </li>
            <li>
              <code>anomalies_detected</code>: {result.anomalies_detected}
            </li>
            <li>
              <code>blocked_events</code>: {result.summary.blocked_events}
            </li>
            <li>
              <code>unique_ips</code>: {result.summary.unique_ips}
            </li>
          </ul>
          <div className="hero-actions">
            <Link href={`/analysis/${result.upload_id}`} className="btn-secondary">
              View Full Analysis
            </Link>
          </div>
        </div>
      ) : null}
    </section>
  );
}
