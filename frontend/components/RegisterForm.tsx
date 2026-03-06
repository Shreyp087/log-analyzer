"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { ApiRequestError, registerUser } from "@/lib/api";
import { clearAuthSession, setAuthSession } from "@/lib/auth";
import type { RegisterRequest } from "@/types";

type RegisterFormState = RegisterRequest & {
  confirmPassword: string;
};

type FeedbackState = {
  type: "idle" | "error" | "success";
  message: string;
};

const INITIAL_FORM: RegisterFormState = {
  email: "",
  password: "",
  confirmPassword: ""
};

export default function RegisterForm() {
  const router = useRouter();
  const [form, setForm] = useState<RegisterFormState>(INITIAL_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackState>({ type: "idle", message: "" });

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setFeedback({ type: "idle", message: "" });

    if (form.password !== form.confirmPassword) {
      setSubmitting(false);
      setFeedback({ type: "error", message: "Passwords do not match." });
      return;
    }

    try {
      const response = await registerUser({ email: form.email, password: form.password });
      setAuthSession(response.access_token, response.user);
      setFeedback({ type: "success", message: `Account created for ${response.user.email}` });
      router.push("/dashboard");
      router.refresh();
    } catch (error) {
      clearAuthSession();
      if (error instanceof ApiRequestError) {
        setFeedback({ type: "error", message: error.message });
      } else {
        setFeedback({ type: "error", message: "Registration failed. Please try again." });
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
          autoComplete="new-password"
          value={form.password}
          onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
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
          value={form.confirmPassword}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, confirmPassword: event.target.value }))
          }
          placeholder="Repeat your password"
        />
      </label>

      <button type="submit" className="btn-primary" disabled={submitting}>
        {submitting ? "Creating Account..." : "Create Account"}
      </button>

      {feedback.type !== "idle" && (
        <p className={`form-feedback ${feedback.type}`}>{feedback.message}</p>
      )}
    </form>
  );
}
