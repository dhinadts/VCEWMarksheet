import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.config import get_settings
from app.core.database import get_db
from app.models.models import (Assessment, MarksheetUpload, OCRExtraction, OCRJob, Professor, ProfessorAssignment,
                               User, UserType)
from app.schemas.common import ok
from app.schemas.ocr import OCRReviewRequest
from app.services.ocr import OpenCVDnnDigitClassifier
from app.services.ocr.digit_recognizer import SyntheticKnnDigitClassifier
from app.services.ocr.structured_pipeline import process_structured_marksheet, question_maximum
from app.storage import get_document_storage

router = APIRouter()
staff = require_roles(UserType.ADMIN, UserType.PROFESSOR)


def ensure_access(db: Session, user: User, upload: MarksheetUpload) -> None:
    if user.user_type == UserType.ADMIN: return
    professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
    assignment = db.scalar(select(ProfessorAssignment).where(ProfessorAssignment.professor_id == professor.id, ProfessorAssignment.course_offering_id == upload.course_offering_id, ProfessorAssignment.active.is_(True)))
    if not assignment: raise HTTPException(403, detail={"code": "UNASSIGNED_COURSE", "message": "This marksheet is outside the professor assignment"})


def extraction_dict(row: OCRExtraction) -> dict:
    return {"id": str(row.id), "field_name": row.field_name, "raw_text": row.raw_text, "numeric_value": float(row.numeric_value) if row.numeric_value is not None else None, "confidence": float(row.confidence), "bounding_box": row.bounding_box_json, "recognizer_version": row.recognizer_version, "requires_review": row.requires_review, "reviewed_value": float(row.reviewed_value) if row.reviewed_value is not None else None, "was_corrected": row.reviewed_value is not None and row.numeric_value != row.reviewed_value, "reviewed_by": str(row.reviewed_by) if row.reviewed_by else None, "reviewed_at": row.reviewed_at}


def response_for(db: Session, upload: MarksheetUpload) -> dict:
    rows = db.scalars(select(OCRExtraction).where(OCRExtraction.marksheet_upload_id == upload.id).order_by(OCRExtraction.field_name)).all()
    return {"marksheet_id": str(upload.id), "processing_status": upload.processing_status, "review_status": upload.review_status, "extractions": [extraction_dict(row) for row in rows]}


@router.post("/marksheets/{marksheet_id}/process")
def process_marksheet(marksheet_id: uuid.UUID, user: User = Depends(staff), db: Session = Depends(get_db)):
    upload = db.get(MarksheetUpload, marksheet_id)
    if not upload: raise HTTPException(404, detail={"code": "MARKSHEET_NOT_FOUND", "message": "Marksheet was not found"})
    ensure_access(db, user, upload)
    existing = db.scalar(select(OCRJob).where(OCRJob.marksheet_upload_id == upload.id))
    if existing and existing.status == "COMPLETED": return ok(response_for(db, upload), "OCR already completed")
    job = existing or OCRJob(marksheet_upload_id=upload.id)
    job.status = "PROCESSING"; job.error_message = None; upload.processing_status = "OCR_PROCESSING"; db.add_all([job, upload]); db.commit()
    try:
        settings = get_settings()
        classifier = OpenCVDnnDigitClassifier(settings.handwriting_model_path) if settings.handwriting_model_path else SyntheticKnnDigitClassifier()
        content = get_document_storage(settings).download(upload.storage_key)
        assessment = db.get(Assessment, upload.assessment_id)
        columns = tuple(int(value.strip()) for value in settings.ocr_mark_column_indices.split(",") if value.strip()) or (-1,)
        debug_directory = Path(settings.document_storage_path) / "debug" / str(upload.id)
        result = process_structured_marksheet(content, classifier, maximum=assessment.maximum_marks, mark_column_indices=columns, debug_directory=debug_directory)
        db.execute(delete(OCRExtraction).where(OCRExtraction.marksheet_upload_id == upload.id))
        for item in result.cells:
            recognition = item.recognition
            db.add(OCRExtraction(marksheet_upload_id=upload.id, field_name=item.field_name, raw_text=recognition.raw_text if recognition else "", numeric_value=recognition.numeric_value if recognition else None, confidence=Decimal(str(recognition.confidence if recognition else 0)), bounding_box_json=item.cell.bounding_box, recognizer_version=classifier.version, requires_review=True))
        job.status = "COMPLETED"; job.recognizer_version = classifier.version
        upload.processing_status = "OCR_COMPLETED"; upload.review_status = "REVIEW_REQUIRED"
        db.add_all([job, upload]); db.commit()
        return ok(response_for(db, upload), "OCR completed; human review is required")
    except Exception as exc:
        db.rollback(); job = db.get(OCRJob, job.id); upload = db.get(MarksheetUpload, upload.id)
        job.status = "FAILED"; job.error_message = str(exc)[:1000]; upload.processing_status = "FAILED"; db.add_all([job, upload]); db.commit()
        raise HTTPException(422, detail={"code": "OCR_PROCESSING_FAILED", "message": "The marks table could not be processed", "details": str(exc)}) from exc


@router.get("/marksheets/{marksheet_id}/ocr")
def get_ocr(marksheet_id: uuid.UUID, user: User = Depends(staff), db: Session = Depends(get_db)):
    upload = db.get(MarksheetUpload, marksheet_id)
    if not upload: raise HTTPException(404, detail={"code": "MARKSHEET_NOT_FOUND", "message": "Marksheet was not found"})
    ensure_access(db, user, upload); return ok(response_for(db, upload))


@router.put("/marksheets/{marksheet_id}/review")
def review_marksheet(marksheet_id: uuid.UUID, body: OCRReviewRequest, user: User = Depends(staff), db: Session = Depends(get_db)):
    upload = db.get(MarksheetUpload, marksheet_id)
    if not upload: raise HTTPException(404, detail={"code": "MARKSHEET_NOT_FOUND", "message": "Marksheet was not found"})
    ensure_access(db, user, upload); assessment = db.get(Assessment, upload.assessment_id)
    corrections = {item.extraction_id: item for item in body.corrections}
    rows = db.scalars(select(OCRExtraction).where(OCRExtraction.marksheet_upload_id == upload.id)).all()
    if not rows: raise HTTPException(409, detail={"code": "OCR_NOT_COMPLETED", "message": "OCR must complete before review"})
    unknown = set(corrections) - {row.id for row in rows}
    if unknown: raise HTTPException(422, detail={"code": "INVALID_EXTRACTION", "message": "A correction does not belong to this marksheet"})
    now = datetime.now(UTC)
    for row in rows:
        correction = corrections.get(row.id)
        final_value = correction.corrected_numeric_value if correction else row.numeric_value
        question_number = int(row.field_name.rsplit("_", 1)[-1]) if row.field_name.startswith("question_") else None
        maximum = question_maximum(question_number, assessment.maximum_marks) if question_number else assessment.maximum_marks
        if final_value is None or final_value < 0 or final_value > maximum:
            raise HTTPException(422, detail={"code": "MARK_EXCEEDS_MAXIMUM", "message": f"{row.field_name} must be between 0 and {maximum}"})
        if question_number and question_number >= 11:
            if not correction or correction.selected_option not in ("A", "B"):
                raise HTTPException(422, detail={"code": "OPTION_REQUIRED", "message": f"Select option A or B for question {question_number}"})
            row.bounding_box_json = {**row.bounding_box_json, "selected_option": correction.selected_option}
        row.reviewed_value = final_value; row.reviewed_by = user.id; row.reviewed_at = now; row.requires_review = False; db.add(row)
    final_total = sum((row.reviewed_value or Decimal("0")) for row in rows)
    if final_total > Decimal("100"):
        raise HTTPException(422, detail={"code": "TOTAL_EXCEEDS_MAXIMUM", "message": "Internal marks total cannot exceed 100"})
    upload.review_status = "REVIEWED"; db.add(upload); db.commit()
    return ok(response_for(db, upload), "OCR review saved")


@router.post("/marksheets/{marksheet_id}/approve")
def approve_marksheet(marksheet_id: uuid.UUID, user: User = Depends(staff), db: Session = Depends(get_db)):
    upload = db.get(MarksheetUpload, marksheet_id)
    if not upload: raise HTTPException(404, detail={"code": "MARKSHEET_NOT_FOUND", "message": "Marksheet was not found"})
    ensure_access(db, user, upload)
    pending = db.scalar(select(OCRExtraction).where(OCRExtraction.marksheet_upload_id == upload.id, OCRExtraction.requires_review.is_(True)))
    if upload.review_status != "REVIEWED" or pending: raise HTTPException(409, detail={"code": "REVIEW_REQUIRED", "message": "All OCR values must be reviewed before approval"})
    upload.review_status = "APPROVED"; upload.processing_status = "APPROVED"; db.add(upload); db.commit()
    return ok(response_for(db, upload), "Marksheet approved")
