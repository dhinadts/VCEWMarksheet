from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Assessment, Course, CourseOffering, MarksheetUpload, OCRExtraction, Student
from app.schemas.common import ok
from app.schemas.student_portal import StudentResultsRequest

router = APIRouter()


@router.post("/results")
def student_results(body: StudentResultsRequest, db: Session = Depends(get_db)):
    roll_number = body.roll_number.strip().upper()
    student = db.scalar(
        select(Student).where(
            (Student.roll_number == roll_number) | (Student.register_number == roll_number),
            Student.active.is_(True),
        )
    )
    if not student:
        raise HTTPException(404, detail={"code": "STUDENT_NOT_FOUND", "message": "No student was found for this roll number"})

    rows = db.execute(
        select(MarksheetUpload, Assessment, Course)
        .join(Assessment, Assessment.id == MarksheetUpload.assessment_id)
        .join(CourseOffering, CourseOffering.id == MarksheetUpload.course_offering_id)
        .join(Course, Course.id == CourseOffering.course_id)
        .where(MarksheetUpload.student_id == student.id, MarksheetUpload.review_status == "APPROVED")
        .order_by(MarksheetUpload.created_at.desc())
    ).all()

    results = []
    for upload, assessment, course in rows:
        extractions = db.scalars(
            select(OCRExtraction)
            .where(OCRExtraction.marksheet_upload_id == upload.id)
            .order_by(OCRExtraction.field_name)
        ).all()
        marks = [
            {
                "question": item.field_name,
                "mark": float(item.reviewed_value if item.reviewed_value is not None else item.numeric_value),
                "option": item.bounding_box_json.get("selected_option"),
            }
            for item in extractions
            if item.reviewed_value is not None or item.numeric_value is not None
        ]
        results.append(
            {
                "marksheet_id": str(upload.id),
                "course_code": course.code,
                "course_name": course.name,
                "assessment": assessment.name,
                "maximum_marks": float(assessment.maximum_marks),
                "marks": marks,
                "total": sum(item["mark"] for item in marks),
                "approved_at": upload.updated_at,
            }
        )

    return ok(
        {
            "student": {
                "roll_number": student.roll_number,
                "register_number": student.register_number,
                "name": student.name,
                "semester": student.current_semester,
                "section": student.section,
            },
            "results": results,
        }
    )
