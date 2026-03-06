import Link from "next/link";

import RegisterForm from "@/components/RegisterForm";

export default function RegisterPage() {
  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="chip">Auth</p>
        <h1>Create Account</h1>
        <p className="subtext">
          Register first to access protected upload and analysis workflows.
        </p>
        <RegisterForm />
        <p className="auth-footer">
          Already have an account? <Link href="/login">Sign in</Link>
        </p>
      </section>
    </main>
  );
}
