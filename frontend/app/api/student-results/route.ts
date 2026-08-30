import { NextResponse } from "next/server";

const apiUrl = process.env.BACKEND_API_URL ?? "http://localhost:8000/api/v1";

export async function POST(request: Request) {
  try {
    const response = await fetch(`${apiUrl}/student-portal/results`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(await request.json()),
      cache: "no-store",
    });
    const text = await response.text();
    const body = text ? JSON.parse(text) : null;
    return NextResponse.json(body ?? { detail: { message: "Empty backend response" } }, { status: response.status });
  } catch {
    return NextResponse.json({ detail: { message: "Cannot reach the backend. Confirm it is running on port 8000." } }, { status: 503 });
  }
}
