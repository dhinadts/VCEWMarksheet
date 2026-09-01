import zipfile
from io import BytesIO
from types import SimpleNamespace

from app.services.department_submission import build_department_zip
from app.storage.local import LocalDocumentStorage


def test_department_zip_contains_original_and_computerized_sheet(tmp_path):
    storage = LocalDocumentStorage(tmp_path)
    storage.upload("marksheets/a/photo.jpg", b"original-photo")
    storage.upload("computerized/a/sheet.csv", b"Question,Mark\nquestion_01,2\n")
    upload = SimpleNamespace(storage_key="marksheets/a/photo.jpg", computerized_storage_key="computerized/a/sheet.csv")
    student = SimpleNamespace(register_number="9130030")

    archive = build_department_zip([(upload, student)], storage)

    with zipfile.ZipFile(BytesIO(archive)) as result:
        assert result.read("9130030/original.jpg") == b"original-photo"
        assert result.read("9130030/computerized-marksheet.csv").startswith(b"Question,Mark")
