import { KeyRound } from "lucide-react";
import { ChangePasswordForm } from "@/components/auth/change-password-form";
export default function ChangePassword(){return <main className="center-shell"><section className="login-card narrow"><div className="brand-mark dark"><KeyRound/></div><p className="eyebrow navy">Account security</p><h1>Choose a new password</h1><p className="muted">Your demo password must be replaced before you can use the system.</p><ChangePasswordForm/></section></main>}
