"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
export function ChangePasswordForm() {
  const router=useRouter(); const [error,setError]=useState(""); const [busy,setBusy]=useState(false);
  async function submit(e:React.FormEvent<HTMLFormElement>){e.preventDefault();setBusy(true);setError("");const d=new FormData(e.currentTarget);if(d.get("new_password")!==d.get("confirm")){setBusy(false);return setError("New passwords do not match");}const r=await fetch("/api/auth/change-password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({current_password:d.get("current_password"),new_password:d.get("new_password")})});const b=await r.json();setBusy(false);if(!r.ok)return setError(b?.detail?.message??b?.error?.message??"Password change failed");router.push("/login?changed=1");}
  return <form onSubmit={submit} className="auth-form"><label>Current password<input name="current_password" type="password" required /></label><label>New password<input name="new_password" type="password" minLength={8} required /></label><label>Confirm new password<input name="confirm" type="password" minLength={8} required /></label>{error&&<p className="form-error">{error}</p>}<button className="primary-button" disabled={busy}>{busy?"Updating…":"Change password"}</button></form>;
}
