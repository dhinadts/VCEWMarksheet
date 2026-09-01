import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.config import get_settings
from app.core.database import get_db
from app.models.models import (Assessment, AuditLog, CourseOffering, Department, MarksheetUpload, Professor, Student,
                               User, UserType)
from app.schemas.common import ok
from app.services.department_submission import build_department_zip, send_department_zip
from app.storage import get_document_storage

router = APIRouter()
staff = require_roles(UserType.ADMIN, UserType.PROFESSOR)


@router.post("/departments/{department_id}/email")
def email_department_marks(
    department_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(staff),
    db: Session = Depends(get_db),
):
    department = db.get(Department, department_id)
    assessment = db.get(Assessment, assessment_id)
    if not department or not assessment:
        raise HTTPException(404, detail={"code": "SUBMISSION_CONTEXT_NOT_FOUND", "message": "Department or assessment was not found"})
    if user.user_type == UserType.PROFESSOR:
        professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
        if not professor or professor.department_id != department_id:
            raise HTTPException(403, detail={"code": "DEPARTMENT_ACCESS_DENIED", "message": "Professors can submit only their own department"})
    query = (
        select(MarksheetUpload, Student)
        .join(Student, Student.id == MarksheetUpload.student_id)
        .join(CourseOffering, CourseOffering.id == MarksheetUpload.course_offering_id)
        .where(
            Student.department_id == department_id,
            MarksheetUpload.assessment_id == assessment_id,
            MarksheetUpload.review_status == "APPROVED",
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
    db.commit()
    return ok({"department_id": str(department.id), "assessment_id": str(assessment.id), "student_count": len(rows), "archive_storage_key": archive_key, "recipient": recipient, "message_id": message_id}, "Department marks emailed to university")
