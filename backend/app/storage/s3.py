from __future__ import annotations

import boto3
from botocore.config import Config


class S3DocumentStorage:
    """Private S3 object storage for original marksheet captures."""

    def __init__(
        self,
        *,
        bucket: str,
        region: str | None,
        access_key_id: str | None,
        secret_access_key: str | None,
        endpoint_url: str | None = None,
        force_path_style: bool = False,
    ) -> None:
        if not bucket:
            raise ValueError("AWS_S3_BUCKET is required when S3 storage is enabled")
        self.bucket = bucket
        addressing_style = "path" if force_path_style else "virtual"
        self.client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            endpoint_url=endpoint_url or None,
            config=Config(s3={"addressing_style": addressing_style}),
        )

    def upload(self, key: str, content: bytes) -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType=_content_type(key),
            ServerSideEncryption="AES256",
        )
        self.client.head_object(Bucket=self.bucket, Key=key)
        return f"s3://{self.bucket}/{key}"

    def download(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


def _content_type(key: str) -> str:
    extension = key.rsplit(".", 1)[-1].lower()
    return {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "csv": "text/csv", "zip": "application/zip"}.get(extension, "application/octet-stream")
