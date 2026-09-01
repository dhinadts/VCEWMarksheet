from __future__ import annotations

import csv
import io
from decimal import Decimal

from app.models.models import Assessment, Course, MarksheetUpload, OCRExtraction, Student


def build_computerized_csv(
    upload: MarksheetUpload,
    student: Student,
    assessment: Assessment,
    course: Course,
    extractions: list[OCRExtraction],
) -> tuple[bytes, Decimal]:
    """Build the immutable, reviewed per-student marksheet stored after approval."""
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["Register Number", student.register_number])
    writer.writerow(["Student Name", student.name])
    writer.writerow(["Course Code", course.code])
    writer.writerow(["Course Title", course.name])
    writer.writerow(["Assessment", assessment.name])
    writer.writerow([])
    writer.writerow(["Question", "Selected Option", "Mark"])
    total = Decimal("0")
    for row in sorted(extractions, key=lambda item: item.field_name):
        value = row.reviewed_value if row.reviewed_value is not None else row.numeric_value
        value = value or Decimal("0")
        total += value
        writer.writerow([row.field_name, row.bounding_box_json.get("selected_option", ""), str(value)])
    writer.writerow([])
    writer.writerow(["Grand Total", "", str(total)])
    return output.getvalue().encode("utf-8-sig"), total
