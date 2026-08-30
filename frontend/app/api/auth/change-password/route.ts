import { cookies } from "next/headers";
import { NextResponse } from "next/server";
const apiUrl = process.env.BACKEND_API_URL ?? "http://localhost:8000/api/v1";
export async function POST(request: Request) {
  const token = (await cookies()).get("access_token")?.value;
  const response = await fetch(`${apiUrl}/auth/change-password`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify(await request.json()) });
  const body = await response.json(); const result = NextResponse.json(body, { status: response.status });
  if (response.ok) { result.cookies.delete("access_token"); result.cookies.delete("refresh_token"); }
  return result;
}
