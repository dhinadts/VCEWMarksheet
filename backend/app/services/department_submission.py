from __future__ import annotations

import io
import zipfile
from email.message import EmailMessage

import boto3

from app.core.config import Settings
from app.models.models import MarksheetUpload, Student


def build_department_zip(rows: list[tuple[MarksheetUpload, Student]], storage) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for upload, student in rows:
            folder = _safe(student.register_number)
            original_extension = upload.storage_key.rsplit(".", 1)[-1]
            archive.writestr(f"{folder}/original.{original_extension}", storage.download(upload.storage_key))
            if upload.computerized_storage_key:
                archive.writestr(f"{folder}/computerized-marksheet.csv", storage.download(upload.computerized_storage_key))
    return buffer.getvalue()


def send_department_zip(settings: Settings, recipient: str, subject: str, filename: str, content: bytes) -> str:
    if not settings.marks_email_sender:
        raise ValueError("MARKS_EMAIL_SENDER is required")
    message = EmailMessage()
    message["From"] = settings.marks_email_sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content("Attached are the approved computerized internal marksheets and their source captures.")
    message.add_attachment(content, maintype="application", subtype="zip", filename=filename)
    client = boto3.client(
        "ses",
        region_name=settings.aws_ses_region or settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
    result = client.send_raw_email(Source=settings.marks_email_sender, Destinations=[recipient], RawMessage={"Data": message.as_bytes()})
    return result["MessageId"]


def _safe(value: str) -> str:
    return "".join(character for character in value if character.isalnum() or character in ("-", "_")) or "student"
