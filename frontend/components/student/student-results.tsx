"use client";

import { useState } from "react";

type Mark = { question: string; mark: number };
type Result = { marksheet_id: string; course_code: string; course_name: string; assessment: string; maximum_marks: number; total: number; marks: Mark[] };
type PortalData = { student: { roll_number: string; register_number: string; name: string; semester: number; section: string }; results: Result[] };

export function StudentResults() {
  const [rollNumber, setRollNumber] = useState("");
  const [data, setData] = useState<PortalData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault(); setLoading(true); setError(""); setData(null);
    try {
      const response = await fetch("/api/student-results", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ roll_number: rollNumber }) });
      const body = await response.json().catch(() => null);
      if (!response.ok) return setError(body?.detail?.message ?? "Unable to find this roll number");
      setData(body.data);
    } catch { setError("Unable to contact the results service."); }
    finally { setLoading(false); }
  }

  return <div className="student-results-shell"><section className="student-results-card">
    <p className="eyebrow navy">Student results portal</p><h1>View internal marks</h1><p className="muted">Enter your VCEW roll number. No password is required.</p>
    <form className="auth-form" onSubmit={submit}><label>Roll number<input value={rollNumber} onChange={event => setRollNumber(event.target.value.toUpperCase())} placeholder="DEMOSTU01" pattern="DEMOSTU(0[1-9]|10)" required autoFocus /></label>{error && <p className="form-error">{error}</p>}<button className="primary-button" disabled={loading}>{loading ? "Loading…" : "View internal marks"}</button></form>
    {data && <div className="student-result-content"><div className="student-summary"><strong>{data.student.name}</strong><span>{data.student.roll_number} · Semester {data.student.semester} · Section {data.student.section}</span></div>{data.results.length === 0 ? <p className="empty-results">No approved internal marks are published yet.</p> : data.results.map(result => <article className="result-card" key={result.marksheet_id}><div><strong>{result.course_code} · {result.course_name}</strong><span>{result.assessment}</span></div><table><thead><tr><th>Question</th><th>Mark</th></tr></thead><tbody>{result.marks.map(mark => <tr key={mark.question}><td>{mark.question}</td><td>{mark.mark}</td></tr>)}<tr><th>Total</th><th>{result.total} / {result.maximum_marks}</th></tr></tbody></table></article>)}</div>}
    <a className="student-back-link" href="/login">Staff sign in</a>
    <style jsx>{`.student-results-shell{min-height:100vh;background:linear-gradient(145deg,#edf4fa,#fff);padding:60px 20px}.student-results-card{width:min(900px,100%);margin:auto;background:#fff;border:1px solid #dce4eb;border-radius:20px;padding:36px;box-shadow:0 18px 48px rgba(16,42,67,.09)}h1{margin:0 0 8px;font-size:2rem}.student-result-content{display:grid;gap:18px;margin-top:32px}.student-summary,.result-card>div{display:flex;justify-content:space-between;gap:16px}.student-summary{padding:18px;background:#eaf2ff;border-radius:12px}.student-summary span,.result-card span{color:#66788a}.result-card{border:1px solid #dce4eb;border-radius:14px;padding:20px}.result-card table{min-width:0;margin-top:16px}.empty-results{padding:24px;background:#f4f7fa;border-radius:12px;color:#66788a}.student-back-link{display:inline-block;margin-top:24px;color:#1f6feb;font-weight:750}@media(max-width:600px){.student-results-card{padding:24px}.student-summary,.result-card>div{flex-direction:column}}`}</style>
  </section></div>;
}
