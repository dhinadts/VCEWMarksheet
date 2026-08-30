import { BookOpenCheck } from "lucide-react";
import { serverApi } from "@/lib/server-api";

type Assessment = { id: string; name: string; maximum_marks: number };
type StudentMark = { total: number | null; status: string; values: { field: string; value: number; confidence: number }[] };
type SubjectStudent = { id: string; register_number: string; roll_number: string; name: string; marks: Record<string, StudentMark> };
type Subject = { id: string; course_code: string; course_name: string; class_code: string; section: string; assessments: Assessment[]; students: SubjectStudent[] };

function statusLabel(status: string) { return status === "NOT_CAPTURED" ? "Not captured" : status.replaceAll("_", " ").toLowerCase(); }

export default async function Page() {
  const subjects = await serverApi<Subject[]>("/my-subjects");
  return <>
    <div className="page-heading"><div><p className="eyebrow navy">Professor workspace</p><h1>My subjects</h1><p>Subjects handled by you and the internal marks of students in each class.</p></div></div>
    {subjects.length === 0 ? <section className="content-card empty-state"><BookOpenCheck/><h2>No subjects assigned</h2><p>Your assigned subjects will appear here.</p></section> : <div className="subject-list">
      {subjects.map(subject => <section className="content-card subject-card" key={subject.id}>
        <div className="subject-heading"><div><span className="subject-code">{subject.course_code}</span><h2>{subject.course_name}</h2></div><span className="badge blue">{subject.class_code} · Section {subject.section}</span></div>
        {subject.assessments.length === 0 ? <p className="empty-table">No internal assessment is configured for this subject.</p> : <div className="table-scroll"><table className="marks-table">
          <thead><tr><th>Register no.</th><th>Roll no.</th><th>Student name</th>{subject.assessments.map(assessment=><th key={assessment.id}>{assessment.name}<small>Max {assessment.maximum_marks}</small></th>)}</tr></thead>
          <tbody>{subject.students.map(student=><tr key={student.id}><td>{student.register_number}</td><td>{student.roll_number}</td><td><strong>{student.name}</strong></td>{subject.assessments.map(assessment=>{const mark=student.marks[assessment.id];return <td key={assessment.id}>{mark?.total == null ? <span className="mark-pending">—<small>{statusLabel(mark?.status ?? "NOT_CAPTURED")}</small></span> : <details className="mark-details"><summary><strong>{mark.total}</strong> / {assessment.maximum_marks}</summary><small>{statusLabel(mark.status)}</small><div className="question-values">{mark.values.map(item=><span key={item.field}>{item.field.replace("question_", "Q")}: <strong>{item.value}</strong></span>)}</div></details>}</td>})}</tr>)}</tbody>
        </table></div>}
      </section>)}
    </div>}
  </>;
}
