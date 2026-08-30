from sqlalchemy import select

from app.models.models import AcademicClass, Assessment, Professor, ProfessorAssignment, User


def test_seed_is_complete_and_idempotent(db):
    from scripts.seed import seed
    first = seed(db); second = seed(db)
    assert first["users"] == second["users"] == 12
    assert first["courses"] == 1


def test_admin_can_create_class(client, admin_headers, db):
    existing = db.scalar(select(AcademicClass))
    payload = {"code": "CST-III-B", "academic_year_id": str(existing.academic_year_id), "department_id": str(existing.department_id), "programme_id": str(existing.programme_id), "semester_id": str(existing.semester_id), "section": "B", "batch": "2025-2029", "strength": 20}
    response = client.post("/api/v1/classes", headers=admin_headers, json=payload)
    assert response.status_code == 201
    assert response.json()["data"]["code"] == "CST-III-B"


def test_course_maxima_are_validated(client, admin_headers, db):
    existing = db.scalar(select(AcademicClass))
    payload = {"programme_id": str(existing.programme_id), "code": "BAD101", "name": "Invalid", "category": "THEORY", "credits": 3, "ca_max": 40, "ese_max": 50, "total_max": 100, "semester_number": 3, "regulation": "2023"}
    response = client.post("/api/v1/courses", headers=admin_headers, json=payload)
    assert response.status_code == 422


def test_professor_only_sees_assigned_offerings(client, professor_headers, db):
    professor_user = db.scalar(select(User).where(User.username == "PROF01"))
    professor = db.scalar(select(Professor).where(Professor.user_id == professor_user.id))
    expected = len(db.scalars(select(ProfessorAssignment).where(ProfessorAssignment.professor_id == professor.id)).all())
    response = client.get("/api/v1/course-offerings", headers=professor_headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) == expected


def test_professor_subjects_include_students_and_internal_marks(client, professor_headers):
    response = client.get("/api/v1/my-subjects", headers=professor_headers)
    assert response.status_code == 200
    subjects = response.json()["data"]
    assert subjects
    assert subjects[0]["course_code"]
    assert subjects[0]["course_name"]
    assert len(subjects[0]["students"]) == 10
    assert "marks" in subjects[0]["students"][0]


def test_professor_master_lists_are_scoped_to_assignments(client, professor_headers, db):
    offerings = client.get("/api/v1/course-offerings", headers=professor_headers).json()["data"]
    expected_course_ids = {row["course_id"] for row in offerings}
    expected_class_ids = {row["class_id"] for row in offerings}
    courses = client.get("/api/v1/courses?page_size=100", headers=professor_headers).json()["data"]["items"]
    classes = client.get("/api/v1/classes?page_size=100", headers=professor_headers).json()["data"]["items"]
    students = client.get("/api/v1/students?page_size=100", headers=professor_headers).json()["data"]["items"]
    assert {row["id"] for row in courses} == expected_course_ids
    assert {row["id"] for row in classes} == expected_class_ids
    assert {row["class_id"] for row in students}.issubset(expected_class_ids)


def test_professor_cannot_create_assessment_for_unassigned_course(client, professor_headers, db):
    professor_user = db.scalar(select(User).where(User.username == "PROF01"))
    professor = db.scalar(select(Professor).where(Professor.user_id == professor_user.id))
    assignment = db.scalar(select(ProfessorAssignment).where(ProfessorAssignment.professor_id == professor.id))
    assessment = db.scalar(select(Assessment).where(Assessment.course_offering_id == assignment.course_offering_id))
    assignment.active = False
    db.commit()
    payload = {"course_offering_id": str(assessment.course_offering_id), "assessment_type_id": str(assessment.assessment_type_id), "name": "Unauthorized Test", "maximum_marks": 20}
    response = client.post("/api/v1/assessments", headers=professor_headers, json=payload)
    assert response.status_code == 403
