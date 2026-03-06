import Link from "next/link";

import LoginForm from "@/components/LoginForm";

export default function LoginPage() {
  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="chip">Stage 9</p>
        <h1>Login</h1>
        <p className="subtext">
          Authenticate first so upload and analysis actions can run through the protected flow.
        </p>
        <LoginForm />
        <p className="auth-footer">
          Return to <Link href="/">dashboard</Link>
        </p>
      </section>
    </main>
  );
}
