"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, LockKeyhole, UserRound } from "lucide-react";

export function LoginForm() {
  const router = useRouter(); const [loading, setLoading] = useState(false); const [error, setError] = useState("");
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoading(true); setError(""); const data = new FormData(event.currentTarget);
    try {
      const response = await fetch("/api/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: data.get("username"), password: data.get("password") }) });
      const body = await response.json().catch(() => null);
      if (!response.ok) return setError(body?.detail?.message ?? "Unable to sign in. Check that the backend is running.");
      router.push(body.must_change_password ? "/change-password" : "/dashboard"); router.refresh();
    } catch {
      setError("Unable to contact the sign-in service.");
    } finally {
      setLoading(false);
    }
  }
  return <form onSubmit={submit} className="auth-form">
    <label>Username or email<div className="input-with-icon"><UserRound size={18}/><input name="username" autoComplete="username" placeholder="ADMIN01" required autoFocus /></div></label>
    <label>Password<div className="input-with-icon"><LockKeyhole size={18}/><input name="password" type="password" autoComplete="current-password" required /></div></label>
    {error && <p className="form-error" role="alert">{error}</p>}
    <button className="primary-button" disabled={loading}>{loading ? "Signing in…" : "Sign in securely"}<ArrowRight size={18}/></button>
  </form>;
}
