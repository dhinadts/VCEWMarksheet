import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.config import get_settings
from app.core.database import get_db
from app.models.models import (AcademicClass, AcademicYear, Assessment, AuditLog, Course, CourseOffering, Department,
                               MarksheetUpload, Professor, ProfessorAssignment, Semester, Student, User, UserType)
from app.schemas.common import ok
from app.services.department_submission import build_department_zip, send_department_zip
from app.storage import get_document_storage

router = APIRouter()
staff = require_roles(UserType.ADMIN, UserType.PROFESSOR)


def serialize_submission(db: Session, upload: MarksheetUpload) -> dict:
    student = db.get(Student, upload.student_id)
    offering = db.get(CourseOffering, upload.course_offering_id)
    course = db.get(Course, offering.course_id)
    year = db.get(AcademicYear, offering.academic_year_id)
    semester = db.get(Semester, offering.semester_id)
    department = db.get(Department, student.department_id)
    return {"id": str(upload.id), "student_name": student.name, "roll_number": student.roll_number,
            "course_code": course.code, "course_name": course.name, "academic_year": year.name,
            "department": department.code, "semester": semester.number,
            "total": float(upload.approved_total) if upload.approved_total is not None else None,
            "status": upload.submission_status, "submitted_at": upload.submitted_to_admin_at}


@router.get("/inbox")
def submission_inbox(user: User = Depends(staff), db: Session = Depends(get_db)):
    query = select(MarksheetUpload).where(MarksheetUpload.review_status == "APPROVED")
    if user.user_type == UserType.PROFESSOR:
        professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
        query = query.join(ProfessorAssignment, ProfessorAssignment.course_offering_id == MarksheetUpload.course_offering_id).where(ProfessorAssignment.professor_id == professor.id)
    rows = db.scalars(query.order_by(MarksheetUpload.updated_at.desc())).all()
    return ok([serialize_submission(db, row) for row in rows])


@router.post("/marksheets/{marksheet_id}/submit-to-admin")
def submit_to_admin(marksheet_id: uuid.UUID, user: User = Depends(require_roles(UserType.PROFESSOR)), db: Session = Depends(get_db)):
    upload = db.get(MarksheetUpload, marksheet_id)
    professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
    assigned = upload and db.scalar(select(ProfessorAssignment).where(ProfessorAssignment.professor_id == professor.id, ProfessorAssignment.course_offering_id == upload.course_offering_id, ProfessorAssignment.active.is_(True)))
    if not upload or not assigned:
        raise HTTPException(404, detail={"code": "MARKSHEET_NOT_FOUND", "message": "Approved marksheet was not found in your assignments"})
    if upload.review_status != "APPROVED" or not upload.computerized_storage_key:
        raise HTTPException(409, detail={"code": "APPROVAL_REQUIRED", "message": "Review and approve the computerized marksheet first"})
    upload.submission_status = "SUBMITTED_TO_ADMIN"; upload.submitted_to_admin_at = datetime.now(UTC)
    db.add(upload); db.commit()
    return ok(serialize_submission(db, upload), "Computerized marksheet submitted to Admin")


@router.post("/marksheets/{marksheet_id}/admin-accept")
def admin_accept(marksheet_id: uuid.UUID, user: User = Depends(require_roles(UserType.ADMIN)), db: Session = Depends(get_db)):
    upload = db.get(MarksheetUpload, marksheet_id)
    if not upload or upload.submission_status != "SUBMITTED_TO_ADMIN":
        raise HTTPException(409, detail={"code": "ADMIN_SUBMISSION_REQUIRED", "message": "The professor must submit this marksheet first"})
    upload.submission_status = "ADMIN_ACCEPTED"; upload.admin_reviewed_by = user.id; upload.admin_reviewed_at = datetime.now(UTC)
    db.add(upload); db.commit()
    return ok(serialize_submission(db, upload), "Marksheet accepted by Admin")


@router.get("/admin-overview")
def admin_overview(academic_year_id: uuid.UUID | None = None, _: User = Depends(require_roles(UserType.ADMIN)), db: Session = Depends(get_db)):
    year = db.get(AcademicYear, academic_year_id) if academic_year_id else db.scalar(select(AcademicYear).order_by(AcademicYear.start_date.desc()))
    class_filter = (AcademicClass.academic_year_id == year.id,) if year else ()
    students = db.scalar(select(func.count()).select_from(Student).join(AcademicClass).where(*class_filter)) or 0
    departments = db.scalar(select(func.count(func.distinct(AcademicClass.department_id))).where(*class_filter)) or 0
    professors = db.scalar(select(func.count()).select_from(Professor).where(Professor.active.is_(True))) or 0
    subjects = db.scalar(select(func.count()).select_from(CourseOffering).where(CourseOffering.academic_year_id == year.id, CourseOffering.active.is_(True))) if year else 0
    submitted = db.scalar(select(func.count()).select_from(MarksheetUpload).where(MarksheetUpload.submission_status == "SUBMITTED_TO_ADMIN")) or 0
    return ok({"academic_year_id": str(year.id) if year else None, "academic_year": year.name if year else "Not configured", "students": students, "departments": departments, "professors": professors, "subjects": subjects or 0, "pending_admin_review": submitted})


@router.post("/departments/{department_id}/email")
def email_department_marks(
    department_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_roles(UserType.ADMIN)),
    db: Session = Depends(get_db),
):
    department = db.get(Department, department_id)
    assessment = db.get(Assessment, assessment_id)
    if not department or not assessment:
        raise HTTPException(404, detail={"code": "SUBMISSION_CONTEXT_NOT_FOUND", "message": "Department or assessment was not found"})
    query = (
        select(MarksheetUpload, Student)
        .join(Student, Student.id == MarksheetUpload.student_id)
        .join(CourseOffering, CourseOffering.id == MarksheetUpload.course_offering_id)
        .where(
            Student.department_id == department_id,
            MarksheetUpload.assessment_id == assessment_id,
            MarksheetUpload.submission_status == "ADMIN_ACCEPTED",
            MarksheetUpload.computerized_storage_key.is_not(None),
        )
        .order_by(Student.register_number)
    )
    rows = list(db.execute(query).all())
    if not rows:
        raise HTTPException(409, detail={"code": "NO_APPROVED_MARKSHEETS", "message": "No approved computerized marksheets are available"})
    settings = get_settings()
    recipient = settings.university_marks_email
    if not recipient:
        raise HTTPException(503, detail={"code": "UNIVERSITY_EMAIL_NOT_CONFIGURED", "message": "UNIVERSITY_MARKS_EMAIL is not configured"})
    storage = get_document_storage(settings)
    archive = build_department_zip(rows, storage)
    filename = f"{department.code}-{assessment.name}-internal-marks.zip".replace(" ", "-")
    archive_key = f"department-submissions/{department.id}/{assessment.id}/{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.zip"
    storage.upload(archive_key, archive)
    try:
        message_id = send_department_zip(settings, recipient, f"{department.code} - {assessment.name} internal marks", filename, archive)
    except Exception as exc:
        raise HTTPException(502, detail={"code": "UNIVERSITY_EMAIL_FAILED", "message": "The ZIP was stored but email delivery failed", "archive_key": archive_key}) from exc
    db.add(AuditLog(actor_user_id=user.id, action="DEPARTMENT_MARKS_EMAILED", entity_type="Department", entity_id=str(department.id), details=f"assessment={assessment.id}; count={len(rows)}; archive={archive_key}; ses_message_id={message_id}"))
    for upload, _student in rows:
        upload.submission_status = "SENT_TO_UNIVERSITY"; db.add(upload)
    db.commit()
    return ok({"department_id": str(department.id), "assessment_id": str(assessment.id), "student_count": len(rows), "archive_storage_key": archive_key, "recipient": recipient, "message_id": message_id}, "Department marks emailed to university")
