import uuid
from types import SimpleNamespace

from app.services.storage_keys import computerized_marksheet_key, original_marksheet_key, student_marksheet_prefix


def test_student_marksheet_keys_are_dynamic_and_hierarchical():
    assessment_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    upload_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    prefix = student_marksheet_prefix(
        SimpleNamespace(name="2026-27"),
        SimpleNamespace(code="CSE"),
        SimpleNamespace(number=5),
        SimpleNamespace(roll_number="23-CS-041"),
    )
    assert prefix == "academic-years/2026-27/departments/CSE/semesters/5/students/23-CS-041"
    assert original_marksheet_key(prefix, assessment_id, upload_id, ".jpg").endswith(
        f"/assessments/{assessment_id}/original/{upload_id}.jpg"
    )
    assert computerized_marksheet_key(prefix, assessment_id, upload_id).endswith(
        f"/assessments/{assessment_id}/computerized/{upload_id}.csv"
    )
