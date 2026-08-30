import { NextResponse } from "next/server";
const apiUrl = process.env.BACKEND_API_URL ?? "http://localhost:8000/api/v1";

export async function POST(request: Request) {
  try {
    const response = await fetch(`${apiUrl}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(await request.json()), cache: "no-store" });
    const text = await response.text();
    const body = text ? JSON.parse(text) : null;
    if (!response.ok) return NextResponse.json(body ?? { detail: { message: "Sign in was rejected by the server" } }, { status: response.status });
    if (!body?.data?.access_token) return NextResponse.json({ detail: { message: "The authentication server returned an invalid response" } }, { status: 502 });
    const result = NextResponse.json({ success: true, must_change_password: body.data.must_change_password });
    result.cookies.set("access_token", body.data.access_token, { httpOnly: true, sameSite: "lax", secure: process.env.NODE_ENV === "production", maxAge: 30 * 60, path: "/" });
    result.cookies.set("refresh_token", body.data.refresh_token, { httpOnly: true, sameSite: "strict", secure: process.env.NODE_ENV === "production", maxAge: 7 * 86400, path: "/" });
    return result;
  } catch {
    return NextResponse.json({ detail: { message: "Cannot reach the backend. Confirm it is running on port 8000." } }, { status: 503 });
  }
}
