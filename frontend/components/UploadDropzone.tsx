"use client";

import Link from "next/link";
import { DragEvent, useMemo, useState } from "react";

import { ApiRequestError, uploadLogFile } from "@/lib/api";
import type { UploadResponse } from "@/types";

type UploadDropzoneProps = {
  onUploaded?: (payload: UploadResponse) => void;
};

export default function UploadDropzone({ onUploaded }: UploadDropzoneProps) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string>("");
  const [result, setResult] = useState<UploadResponse | null>(null);

  const selectedFileLabel = useMemo(() => {
    if (!file) return "No file selected";
    return `${file.name} (${Math.ceil(file.size / 1024)} KB)`;
  }, [file]);

  const onDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);

    const candidate = event.dataTransfer.files?.[0];
    if (!candidate) return;
    setFile(candidate);
    setError("");
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
      setError("Please select a log file before uploading.");
      return;
    }

    setUploading(true);
    setError("");

    try {
      const payload = await uploadLogFile(file, "zscaler");
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
      setUploading(false);
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
          onChange={(event) => {
            const candidate = event.target.files?.[0];
            if (candidate) {
              setFile(candidate);
              setError("");
            }
          }}
        />
        <strong>Drop Zscaler log file here</strong>
        <span>or click to browse</span>
      </label>

      <p className="muted">{selectedFileLabel}</p>

      <button type="button" className="btn-primary" onClick={submitUpload} disabled={uploading}>
        {uploading ? "Uploading..." : "Upload And Analyze"}
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
