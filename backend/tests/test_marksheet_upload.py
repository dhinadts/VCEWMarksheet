import uuid

import cv2
import numpy as np
from sqlalchemy import select

from app.core.config import get_settings
from app.models.models import Assessment, CourseOffering, Professor, ProfessorAssignment, Student, User


def context_for_professor(db, username="PROF01"):
    user = db.scalar(select(User).where(User.username == username))
    professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
    assignment = db.scalar(select(ProfessorAssignment).where(ProfessorAssignment.professor_id == professor.id))
    offering = db.get(CourseOffering, assignment.course_offering_id)
    assessment = db.scalar(select(Assessment).where(Assessment.course_offering_id == offering.id))
    student = db.scalar(select(Student).where(Student.class_id == offering.class_id))
    return student, offering, assessment


def image_bytes():
    image = np.full((900, 700, 3), 35, dtype=np.uint8)
    page = np.array([[70, 55], [645, 85], [620, 850], [45, 820]], dtype=np.int32)
    cv2.fillConvexPoly(image, page, (242, 242, 242))
    for y in range(160, 760, 55):
        cv2.line(image, (100, y), (575, y + 8), (45, 45, 45), 2)
    for x in range(100, 600, 95):
        cv2.line(image, (x, 145), (x - 15, 775), (70, 70, 70), 2)
    cv2.putText(image, "12  08  15", (130, 130), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (10, 10, 10), 2)
    encoded, data = cv2.imencode(".jpg", image)
    assert encoded
    return data.tobytes()


def test_staff_upload_is_private_idempotent_and_duplicate_safe(client, professor_headers, db, tmp_path):
    get_settings().document_storage_path = str(tmp_path)
    student, offering, assessment = context_for_professor(db)
    request_id = str(uuid.uuid4())
    form = {"student_id": str(student.id), "course_offering_id": str(offering.id), "assessment_id": str(assessment.id), "client_request_id": request_id}
    files = {"file": ("capture.jpg", image_bytes(), "image/jpeg")}
    first = client.post("/api/v1/marksheets", headers=professor_headers, data=form, files=files)
    assert first.status_code == 201
    assert first.json()["data"]["processing_status"] == "UPLOADED"
    assert first.json()["data"]["capture_quality_json"]["acceptable"] is True
    assert (tmp_path / first.json()["data"]["storage_key"]).is_file()
    replay = client.post("/api/v1/marksheets", headers=professor_headers, data=form, files=files)
    assert replay.status_code == 201
    assert replay.json()["data"]["id"] == first.json()["data"]["id"]
    duplicate_form = {**form, "client_request_id": str(uuid.uuid4())}
    duplicate = client.post("/api/v1/marksheets", headers=professor_headers, data=duplicate_form, files=files)
    assert duplicate.status_code == 409


def test_student_cannot_upload_marksheet(client, student_headers):
    response = client.post("/api/v1/marksheets", headers=student_headers, data={})
    assert response.status_code in (403, 422)


def test_blurry_capture_is_rejected_before_storage(client, professor_headers, db, tmp_path):
    get_settings().document_storage_path = str(tmp_path)
    student, offering, assessment = context_for_professor(db)
    blurred = cv2.GaussianBlur(cv2.imdecode(np.frombuffer(image_bytes(), np.uint8), cv2.IMREAD_COLOR), (81, 81), 0)
    _, encoded = cv2.imencode(".jpg", blurred)
    form = {"student_id": str(student.id), "course_offering_id": str(offering.id), "assessment_id": str(assessment.id), "client_request_id": str(uuid.uuid4())}
    response = client.post("/api/v1/marksheets", headers=professor_headers, data=form, files={"file": ("blurred.jpg", encoded.tobytes(), "image/jpeg")})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INSUFFICIENT_IMAGE_QUALITY"
