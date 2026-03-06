"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { ApiRequestError, loginUser } from "@/lib/api";
import { clearAuthSession, setAuthSession } from "@/lib/auth";
import type { LoginRequest } from "@/types";

type FeedbackState = {
  type: "idle" | "error" | "success";
  message: string;
};

const INITIAL_FORM: LoginRequest = {
  email: "",
  password: ""
};

export default function LoginForm() {
  const router = useRouter();
  const [form, setForm] = useState<LoginRequest>(INITIAL_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackState>({ type: "idle", message: "" });

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setFeedback({ type: "idle", message: "" });

    try {
      const response = await loginUser(form);
      setAuthSession(response.access_token, response.user);
      setFeedback({ type: "success", message: `Logged in as ${response.user.email}` });
      router.push("/");
      router.refresh();
    } catch (error) {
      clearAuthSession();
      if (error instanceof ApiRequestError) {
        setFeedback({ type: "error", message: error.message });
      } else {
        setFeedback({ type: "error", message: "Login failed. Please try again." });
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="auth-form" onSubmit={onSubmit}>
      <label className="field">
        <span>Email</span>
        <input
          className="input"
          type="email"
          required
          autoComplete="email"
          value={form.email}
          onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
          placeholder="analyst@company.com"
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
          value={form.password}
          onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
          placeholder="********"
        />
      </label>

      <button type="submit" className="btn-primary" disabled={submitting}>
        {submitting ? "Signing In..." : "Sign In"}
      </button>

      {feedback.type !== "idle" && (
        <p className={`form-feedback ${feedback.type}`}>{feedback.message}</p>
      )}
    </form>
  );
}
