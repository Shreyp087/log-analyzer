"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { fetchCurrentUser } from "@/lib/api";
import { clearAuthSession, getAuthSession } from "@/lib/auth";
import type { AuthenticatedUser } from "@/types";

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const session = getAuthSession();
    if (!session) {
      router.replace("/login");
      return;
    }

    fetchCurrentUser(session.token)
      .then((currentUser) => {
        setUser(currentUser);
      })
      .catch(() => {
        clearAuthSession();
        setError("Session expired. Please login again.");
        router.replace("/login");
      })
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <p className="muted">Loading dashboard...</p>
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <section className="hero">
        <p className="chip">Stage 10</p>
        <h1>Dashboard</h1>
        {user ? (
          <p className="subtext">
            Logged in as <strong>{user.email}</strong> ({user.role}).
          </p>
        ) : (
          <p className="subtext">Authenticated workspace for upload and analysis actions.</p>
        )}
        {error ? <p className="form-feedback error">{error}</p> : null}
      </section>

      <section className="grid">
        <article className="card">
          <h2>Primary Action</h2>
          <p className="muted">
            Upload a Zscaler log to run parse, summary, and anomaly detection in one flow.
          </p>
          <div className="hero-actions">
            <Link href="/upload" className="btn-secondary">
              Go To Upload
            </Link>
          </div>
        </article>

        <article className="card">
          <h2>Session Controls</h2>
          <div className="hero-actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => {
                clearAuthSession();
                router.push("/login");
              }}
            >
              Logout
            </button>
          </div>
        </article>
      </section>
    </main>
  );
}
