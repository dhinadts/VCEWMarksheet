"""Load the supplied PROF01 reference marksheet after storing it in S3.

The reference values are human-verified from the supplied image. They provide
an end-to-end baseline while automatic OCR remains review-first.
"""

import hashlib
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models.models import (Assessment, MarksheetUpload, OCRExtraction, Professor, ProfessorAssignment,
                               Student, User)
from app.services.ocr import preprocess_marksheet
from app.storage import get_document_storage

REFERENCE_VALUES = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 12, 13, 12, 12, 7, 12]


def seed_reference_marksheet(image_path: str | Path = "../docs/MarkSheet.jpeg") -> MarksheetUpload:
    path = Path(image_path).resolve()
    content = path.read_bytes()
    checksum = hashlib.sha256(content).hexdigest()
    quality = preprocess_marksheet(content).quality.as_dict()

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "PROF01"))
        professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
        assignment = db.scalar(
            select(ProfessorAssignment)
            .where(ProfessorAssignment.professor_id == professor.id, ProfessorAssignment.active.is_(True))
            .order_by(ProfessorAssignment.created_at.desc())
        )
        assessment = db.scalar(select(Assessment).where(Assessment.course_offering_id == assignment.course_offering_id))
        student = db.scalar(select(Student).where(Student.roll_number == "VCEW1001"))
        if not all((user, professor, assignment, assessment, student)):
            raise RuntimeError("Run scripts.seed before loading the reference marksheet")

        upload = db.scalar(select(MarksheetUpload).where(MarksheetUpload.checksum_sha256 == checksum))
        upload_id = upload.id if upload else uuid.uuid4()
        storage_key = f"marksheets/{assessment.id}/{upload_id}.jpg"

        # This must complete before any OCR/extraction record is written.
        get_document_storage().upload(storage_key, content)

        if not upload:
            upload = MarksheetUpload(
                id=upload_id,
                student_id=student.id,
                assessment_id=assessment.id,
                course_offering_id=assignment.course_offering_id,
                uploaded_by=user.id,
                source="REFERENCE_IMPORT",
                original_filename=path.name,
                storage_key=storage_key,
                mime_type="image/jpeg",
                checksum_sha256=checksum,
                size_bytes=len(content),
                capture_quality_json=quality,
                processing_status="OCR_COMPLETED",
                review_status="APPROVED",
                client_request_id="prof01-reference-marksheet",
            )
            db.add(upload)
        else:
            upload.storage_key = storage_key
            upload.student_id = student.id
            upload.assessment_id = assessment.id
            upload.course_offering_id = assignment.course_offering_id
            upload.processing_status = "OCR_COMPLETED"
            upload.review_status = "APPROVED"
            upload.capture_quality_json = quality

        db.flush()
        db.execute(delete(OCRExtraction).where(OCRExtraction.marksheet_upload_id == upload.id))
        reviewed_at = datetime.now(UTC)
        for index, value in enumerate(REFERENCE_VALUES, 1):
            numeric = Decimal(value)
            db.add(OCRExtraction(
                marksheet_upload_id=upload.id,
                field_name=f"question_{index:02d}",
                raw_text=str(value),
                numeric_value=numeric,
                confidence=Decimal("1.0000"),
                bounding_box_json={"reference_import": True},
                recognizer_version="human-verified-reference-v1",
                requires_review=False,
                reviewed_value=numeric,
                reviewed_by=user.id,
                reviewed_at=reviewed_at,
            ))
        db.commit()
        db.refresh(upload)
        return upload


def main() -> None:
    upload = seed_reference_marksheet()
    print({"marksheet_id": str(upload.id), "storage_key": upload.storage_key, "total": sum(REFERENCE_VALUES)})


if __name__ == "__main__":
    main()
