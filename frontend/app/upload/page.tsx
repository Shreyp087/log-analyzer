"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import UploadDropzone from "@/components/UploadDropzone";
import { getAuthToken } from "@/lib/auth";

export default function UploadPage() {
  const router = useRouter();

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      router.replace("/");
    }
  }, [router]);

  return (
    <main className="shell">
      <section className="hero">
        <p className="chip">Log Upload</p>
        <h1>Upload Logs</h1>
        <p className="subtext">
          Submit a Zscaler log file and run parser, summary generation, and anomaly detection
          through the authenticated backend workflow.
        </p>
        <div className="hero-actions">
          <Link href="/dashboard" className="btn-secondary">
            Back To Dashboard
          </Link>
        </div>
      </section>

      <UploadDropzone />
    </main>
  );
}
