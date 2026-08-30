import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";
const apiUrl = process.env.BACKEND_API_URL ?? "http://localhost:8000/api/v1";
async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const token = (await cookies()).get("access_token")?.value;
  if (!token) return NextResponse.json({ error: { message: "Authentication required" } }, { status: 401 });
  const { path } = await context.params; const url = `${apiUrl}/${path.join("/")}${request.nextUrl.search}`;
  const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.text();
  const response = await fetch(url, { method: request.method, headers: { "Content-Type": request.headers.get("content-type") ?? "application/json", Authorization: `Bearer ${token}` }, body, cache: "no-store" });
  return new NextResponse(await response.text(), { status: response.status, headers: { "Content-Type": response.headers.get("content-type") ?? "application/json" } });
}
export const GET = proxy; export const POST = proxy; export const PUT = proxy; export const PATCH = proxy; export const DELETE = proxy;
