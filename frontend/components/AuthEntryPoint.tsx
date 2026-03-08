"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiRequestError, loginUser, registerUser } from "@/lib/api";
import { clearAuthSession, setAuthSession } from "@/lib/auth";
import type { LoginRequest, RegisterRequest } from "@/types";

type AuthTab = "signin" | "signup";

type FeedbackState = {
  type: "idle" | "error" | "success";
  message: string;
};

const DEFAULT_SIGNIN: LoginRequest = {
  username: "",
  password: "",
};

const DEFAULT_SIGNUP: RegisterRequest & { confirmPassword: string } = {
  name: "",
  username: "",
  password: "",
  confirmPassword: "",
  role: "SOC Analyst",
};

const ROLE_OPTIONS: RegisterRequest["role"][] = [
  "SOC Analyst",
  "Security Admin",
  "Threat Hunter",
  "IR Analyst",
];

function resolveToken(payload: { token?: string; access_token?: string }): string {
  return payload.token || payload.access_token || "";
}

export default function AuthEntryPoint() {
  const router = useRouter();
  const [tab, setTab] = useState<AuthTab>("signin");
  const [signinForm, setSigninForm] = useState<LoginRequest>(DEFAULT_SIGNIN);
  const [signupForm, setSignupForm] = useState(DEFAULT_SIGNUP);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackState>({ type: "idle", message: "" });

  const submitSignIn = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setFeedback({ type: "idle", message: "" });

    try {
      const response = await loginUser(signinForm);
      const token = resolveToken(response);
      setAuthSession(token, response.user);
      router.push("/dashboard");
      router.refresh();
    } catch (error) {
      clearAuthSession();
      if (error instanceof ApiRequestError) {
        setFeedback({ type: "error", message: error.message });
      } else {
        setFeedback({ type: "error", message: "Sign in failed. Please try again." });
      }
    } finally {
      setSubmitting(false);
    }
  };

  const submitSignUp = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setFeedback({ type: "idle", message: "" });

    if (signupForm.username.trim().length < 3) {
      setSubmitting(false);
      setFeedback({ type: "error", message: "Username must be at least 3 characters." });
      return;
    }

    if (signupForm.password.length < 8) {
      setSubmitting(false);
      setFeedback({ type: "error", message: "Password must be at least 8 characters." });
      return;
    }

    if (signupForm.password !== signupForm.confirmPassword) {
      setSubmitting(false);
      setFeedback({ type: "error", message: "Passwords do not match." });
      return;
    }

    try {
      const response = await registerUser({
        name: signupForm.name.trim(),
        username: signupForm.username.trim().toLowerCase(),
        password: signupForm.password,
        role: signupForm.role,
      });
      const token = resolveToken(response);
      setAuthSession(token, response.user);
      router.push("/dashboard");
      router.refresh();
    } catch (error) {
      clearAuthSession();
      if (error instanceof ApiRequestError) {
        if (error.status === 409) {
          setFeedback({ type: "error", message: "Username already taken" });
        } else {
          setFeedback({ type: "error", message: error.message });
        }
      } else {
        setFeedback({ type: "error", message: "Registration failed. Please try again." });
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="chip">Auth</p>
        <h1>Log Analyzer Access</h1>
        <p className="subtext">Sign in or create an account to access upload and analysis tools.</p>

        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab ${tab === "signin" ? "active" : ""}`}
            onClick={() => {
              setFeedback({ type: "idle", message: "" });
              setTab("signin");
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab ${tab === "signup" ? "active" : ""}`}
            onClick={() => {
              setFeedback({ type: "idle", message: "" });
              setTab("signup");
            }}
          >
            Create Account
          </button>
        </div>

        {tab === "signin" ? (
          <form className="auth-form" onSubmit={submitSignIn}>
            <label className="field">
              <span>Username</span>
              <input
                className="input"
                type="text"
                required
                autoComplete="username"
                value={signinForm.username}
                onChange={(event) =>
                  setSigninForm((prev) => ({ ...prev, username: event.target.value }))
                }
                placeholder="analyst"
              />
            </label>

            <label className="field">
              <span>Password</span>
              <input
                className="input"
                type="password"
                required
                minLength={8}
                autoComplete="current-password"
                value={signinForm.password}
                onChange={(event) =>
                  setSigninForm((prev) => ({ ...prev, password: event.target.value }))
                }
                placeholder="********"
              />
            </label>

            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Signing In..." : "Sign In"}
            </button>
          </form>
        ) : (
          <form className="auth-form" onSubmit={submitSignUp}>
            <label className="field">
              <span>Full Name</span>
              <input
                className="input"
                type="text"
                required
                autoComplete="name"
                value={signupForm.name}
                onChange={(event) => setSignupForm((prev) => ({ ...prev, name: event.target.value }))}
                placeholder="Alex Morgan"
              />
            </label>

            <label className="field">
              <span>Username</span>
              <input
                className="input"
                type="text"
                required
                minLength={3}
                autoComplete="username"
                value={signupForm.username}
                onChange={(event) =>
                  setSignupForm((prev) => ({ ...prev, username: event.target.value }))
                }
                placeholder="alex.morgan"
              />
            </label>

            <label className="field">
              <span>Password</span>
              <input
                className="input"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={signupForm.password}
                onChange={(event) =>
                  setSignupForm((prev) => ({ ...prev, password: event.target.value }))
                }
                placeholder="At least 8 characters"
              />
            </label>

            <label className="field">
              <span>Confirm Password</span>
              <input
                className="input"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={signupForm.confirmPassword}
                onChange={(event) =>
                  setSignupForm((prev) => ({ ...prev, confirmPassword: event.target.value }))
                }
                placeholder="Repeat your password"
              />
            </label>

            <label className="field">
              <span>Role</span>
              <select
                className="input"
                value={signupForm.role}
                onChange={(event) =>
                  setSignupForm((prev) => ({
                    ...prev,
                    role: event.target.value as RegisterRequest["role"],
                  }))
                }
              >
                {ROLE_OPTIONS.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
            </label>

            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Creating Account..." : "Create Account"}
            </button>
          </form>
        )}

        {feedback.type !== "idle" ? (
          <p className={`form-feedback ${feedback.type}`}>{feedback.message}</p>
        ) : null}
      </section>
    </main>
  );
}
