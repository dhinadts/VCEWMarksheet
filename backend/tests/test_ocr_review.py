from decimal import Decimal

from app.api.v1.routes import ocr as ocr_route
from app.services.ocr.digit_recognizer import NumericRecognitionResult, RecognizedGlyph
from app.services.ocr.grid_detector import CellRegion
from app.services.ocr.structured_pipeline import CellOCRResult, StructuredOCRResult
from tests.test_marksheet_upload import context_for_professor, image_bytes


class FakeClassifier:
    version = "test-offline-model-v1"


def test_process_review_correction_and_approval_preserve_raw_value(client, professor_headers, db, tmp_path, monkeypatch):
    from app.core.config import get_settings
    get_settings().document_storage_path = str(tmp_path)
    student, offering, assessment = context_for_professor(db)
    upload = client.post("/api/v1/marksheets", headers=professor_headers, data={"student_id": str(student.id), "course_offering_id": str(offering.id), "assessment_id": str(assessment.id)}, files={"file": ("capture.jpg", image_bytes(), "image/jpeg")})
    marksheet_id = upload.json()["data"]["id"]
    recognition = NumericRecognitionResult("12", Decimal("12"), 0.71, True, FakeClassifier.version, (RecognizedGlyph("1", 0.72, (1, 1, 10, 20)), RecognizedGlyph("2", 0.70, (12, 1, 12, 20))))
    fake_result = StructuredOCRResult((CellOCRResult("cell_r001_c002", CellRegion(1, 2, 10, 20, 80, 40), recognition, None),), 2, 3)
    monkeypatch.setattr(ocr_route, "SyntheticKnnDigitClassifier", FakeClassifier)
    monkeypatch.setattr(ocr_route, "process_structured_marksheet", lambda *args, **kwargs: fake_result)
    processed = client.post(f"/api/v1/marksheets/{marksheet_id}/process", headers=professor_headers)
    assert processed.status_code == 200
    extraction = processed.json()["data"]["extractions"][0]
    assert extraction["raw_text"] == "12" and extraction["numeric_value"] == 12.0
    assert client.post(f"/api/v1/marksheets/{marksheet_id}/approve", headers=professor_headers).status_code == 409
    reviewed = client.put(f"/api/v1/marksheets/{marksheet_id}/review", headers=professor_headers, json={"corrections": [{"extraction_id": extraction["id"], "corrected_numeric_value": 13}]})
    saved = reviewed.json()["data"]["extractions"][0]
    assert saved["raw_text"] == "12" and saved["numeric_value"] == 12.0
    assert saved["reviewed_value"] == 13.0 and saved["was_corrected"] is True
    approved = client.post(f"/api/v1/marksheets/{marksheet_id}/approve", headers=professor_headers)
    assert approved.status_code == 200
    assert approved.json()["data"]["review_status"] == "APPROVED"
