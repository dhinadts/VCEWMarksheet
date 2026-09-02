from __future__ import annotations

import re
import uuid

from app.models.models import AcademicYear, Department, Semester, Student


def student_marksheet_prefix(
    academic_year: AcademicYear,
    department: Department,
    semester: Semester,
    student: Student,
) -> str:
    """Return the dynamic, human-readable S3 prefix for one student's marksheets."""
    return "/".join(
        (
            "academic-years",
            _segment(academic_year.name),
            "departments",
            _segment(department.code),
            "semesters",
            _segment(str(semester.number)),
            "students",
            _segment(student.roll_number),
        )
    )


def original_marksheet_key(prefix: str, assessment_id: uuid.UUID, upload_id: uuid.UUID, extension: str) -> str:
    return f"{prefix}/assessments/{assessment_id}/original/{upload_id}{extension}"


def computerized_marksheet_key(prefix: str, assessment_id: uuid.UUID, upload_id: uuid.UUID) -> str:
    return f"{prefix}/assessments/{assessment_id}/computerized/{upload_id}.csv"


def _segment(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-.")
    if not cleaned:
        raise ValueError("Storage hierarchy values cannot be empty")
    return cleaned
