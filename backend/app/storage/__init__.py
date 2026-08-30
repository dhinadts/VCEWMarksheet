from app.core.config import Settings, get_settings
from app.storage.local import LocalDocumentStorage
from app.storage.s3 import S3DocumentStorage


def get_document_storage(settings: Settings | None = None):
    settings = settings or get_settings()
    if settings.uses_s3:
        return S3DocumentStorage(
            bucket=settings.aws_s3_bucket or "",
            region=settings.aws_region,
            access_key_id=settings.aws_access_key_id,
            secret_access_key=settings.aws_secret_access_key,
            endpoint_url=settings.aws_s3_endpoint,
            force_path_style=settings.aws_s3_force_path_style,
        )
    return LocalDocumentStorage(settings.document_storage_path)


__all__ = ["LocalDocumentStorage", "S3DocumentStorage", "get_document_storage"]
