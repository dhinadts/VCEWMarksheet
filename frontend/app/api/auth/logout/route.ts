import { cookies } from "next/headers";
import { NextResponse } from "next/server";
const apiUrl = process.env.BACKEND_API_URL ?? "http://localhost:8000/api/v1";
export async function POST() {
  const store = await cookies(); const refresh = store.get("refresh_token")?.value;
  if (refresh) await fetch(`${apiUrl}/auth/logout`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: refresh }) }).catch(() => undefined);
  const response = NextResponse.json({ success: true });
  response.cookies.delete("access_token"); response.cookies.delete("refresh_token");
  return response;
}
