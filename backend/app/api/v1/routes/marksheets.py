import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.config import get_settings
from app.core.database import get_db
from app.models.models import (AcademicYear, Assessment, Department, CourseOffering, MarksheetUpload, Professor,
                               ProfessorAssignment, Semester, Student, User, UserType)
from app.schemas.common import ok
from app.services.ocr import preprocess_marksheet
from app.services.storage_keys import original_marksheet_key, student_marksheet_prefix
from app.storage import get_document_storage

router = APIRouter()
staff = require_roles(UserType.ADMIN, UserType.PROFESSOR)
ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024


def serialize(row: MarksheetUpload) -> dict:
    return {column.name: str(getattr(row, column.name)) if isinstance(getattr(row, column.name), uuid.UUID) else getattr(row, column.name) for column in row.__table__.columns}


@router.post("", status_code=201)
async def upload_marksheet(
    student_id: uuid.UUID = Form(),
    assessment_id: uuid.UUID = Form(),
    course_offering_id: uuid.UUID = Form(),
    client_request_id: str | None = Form(default=None),
    source: str = Form(default="MOBILE_CAMERA"),
    file: UploadFile = File(),
    user: User = Depends(staff),
    db: Session = Depends(get_db),
):
    if client_request_id:
        existing_request = db.scalar(select(MarksheetUpload).where(MarksheetUpload.client_request_id == client_request_id))
        if existing_request:
            return ok(serialize(existing_request), "Existing upload returned")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, detail={"code": "UNSUPPORTED_IMAGE_TYPE", "message": "Only JPEG, PNG, and WebP images are accepted"})
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if not content or len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, detail={"code": "INVALID_IMAGE_SIZE", "message": "Image must be between 1 byte and 15 MB"})
    try:
        preprocessing = preprocess_marksheet(content)
    except ValueError as exc:
        raise HTTPException(422, detail={"code": "INSUFFICIENT_IMAGE_QUALITY", "message": "Image quality is insufficient. Please capture the marksheet again.", "details": str(exc)}) from exc
    assessment = db.get(Assessment, assessment_id)
    offering = db.get(CourseOffering, course_offering_id)
    student = db.get(Student, student_id)
    if not assessment or not offering or not student or assessment.course_offering_id != offering.id or student.class_id != offering.class_id:
        raise HTTPException(422, detail={"code": "INVALID_MARKSHEET_CONTEXT", "message": "Student, course offering, and assessment do not belong together"})
    if user.user_type == UserType.PROFESSOR:
        professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
        assigned = db.scalar(select(ProfessorAssignment).where(ProfessorAssignment.professor_id == professor.id, ProfessorAssignment.course_offering_id == offering.id, ProfessorAssignment.active.is_(True)))
        if not assigned:
            raise HTTPException(403, detail={"code": "UNASSIGNED_COURSE", "message": "Professor is not assigned to this course offering"})
    checksum = hashlib.sha256(content).hexdigest()
    duplicate = db.scalar(select(MarksheetUpload).where(MarksheetUpload.checksum_sha256 == checksum))
    if duplicate:
        raise HTTPException(409, detail={"code": "DUPLICATE_MARKSHEET", "message": "Possible duplicate marksheet detected", "existing_id": str(duplicate.id)})
    upload_id = uuid.uuid4()
    extension = ALLOWED_TYPES[file.content_type]
    academic_year = db.get(AcademicYear, offering.academic_year_id)
    department = db.get(Department, student.department_id)
    semester = db.get(Semester, offering.semester_id)
    prefix = student_marksheet_prefix(academic_year, department, semester, student)
    storage_key = original_marksheet_key(prefix, assessment_id, upload_id, extension)
    storage = get_document_storage(get_settings())
    storage.upload(storage_key, content)
    row = MarksheetUpload(id=upload_id, student_id=student_id, assessment_id=assessment_id, course_offering_id=course_offering_id, uploaded_by=user.id, source=source, original_filename=Path(file.filename or f"capture{extension}").name, storage_key=storage_key, mime_type=file.content_type, checksum_sha256=checksum, size_bytes=len(content), capture_quality_json=preprocessing.quality.as_dict(), client_request_id=client_request_id)
    try:
        db.add(row); db.commit(); db.refresh(row)
    except Exception:
        db.rollback(); storage.delete(storage_key); raise
    return ok(serialize(row), "Marksheet uploaded")


@router.get("")
def list_marksheets(user: User = Depends(staff), db: Session = Depends(get_db)):
    query = select(MarksheetUpload).order_by(MarksheetUpload.created_at.desc())
    if user.user_type == UserType.PROFESSOR:
        professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
        query = query.join(CourseOffering, MarksheetUpload.course_offering_id == CourseOffering.id).join(ProfessorAssignment).where(ProfessorAssignment.professor_id == professor.id)
    return ok([serialize(row) for row in db.scalars(query).all()])
