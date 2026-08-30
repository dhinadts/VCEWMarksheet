import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ApiSuccess, SessionUser, UserRole } from "./types";

const apiUrl = process.env.BACKEND_API_URL ?? "http://localhost:8000/api/v1";

export async function serverApi<T>(path: string): Promise<T> {
  const token = (await cookies()).get("access_token")?.value;
  if (!token) redirect("/login");
  const response = await fetch(`${apiUrl}${path}`, { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" });
  if (response.status === 401) redirect("/login");
  if (!response.ok) throw new Error(`API request failed: ${response.status}`);
  return ((await response.json()) as ApiSuccess<T>).data;
}

export async function requireUser(roles?: UserRole[]): Promise<SessionUser> {
  const user = await serverApi<SessionUser>("/auth/me");
  if (user.must_change_password) redirect("/change-password");
  if (roles && !roles.includes(user.user_type)) redirect(`/${user.user_type.toLowerCase()}`);
  return user;
}
