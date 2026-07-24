"""Storage service for MinIO integration."""

import hashlib
import uuid
from datetime import datetime
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.config import get_settings

settings = get_settings()

# MinIO bucket definitions
BUCKETS = {
    "original-artwork": "Original artwork uploads",
    "master-artwork": "Master artwork files",
    "variants": "Artwork variants",
    "reports": "Generated reports",
    "exports": "Export files",
    "temporary": "Temporary files",
}


class StorageService:
    """Handles MinIO storage operations."""

    def __init__(self):
        self.client = Minio(
            f"{settings.minio_host}:{settings.minio_port}",
            access_key=settings.minio_root_user,
            secret_key=settings.minio_root_password,
            secure=False,
        )

    def initialize_buckets(self) -> None:
        """Create all required buckets if they don't exist."""
        for bucket_name in BUCKETS:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)

    def upload_file(
        self,
        bucket: str,
        file_data: bytes,
        original_filename: str,
        content_type: str,
    ) -> dict:
        """Upload a file to MinIO and return metadata."""
        file_id = str(uuid.uuid4())
        extension = original_filename.rsplit(".", 1)[-1] if "." in original_filename else ""
        storage_path = f"{datetime.utcnow().strftime('%Y/%m/%d')}/{file_id}.{extension}"
        checksum = hashlib.sha256(file_data).hexdigest()

        from io import BytesIO

        file_stream = BytesIO(file_data)
        self.client.put_object(
            bucket,
            storage_path,
            file_stream,
            length=len(file_data),
            content_type=content_type,
        )

        return {
            "file_id": file_id,
            "filename": f"{file_id}.{extension}",
            "original_filename": original_filename,
            "content_type": content_type,
            "file_size": len(file_data),
            "bucket": bucket,
            "storage_path": storage_path,
            "checksum": checksum,
        }

    def get_file_url(self, bucket: str, storage_path: str, expires_hours: int = 1) -> str:
        """Get a presigned URL for file download."""
        from datetime import timedelta

        url = self.client.presigned_get_object(
            bucket, storage_path, expires=timedelta(hours=expires_hours)
        )
        return url

    def delete_file(self, bucket: str, storage_path: str) -> bool:
        """Delete a file from storage."""
        try:
            self.client.remove_object(bucket, storage_path)
            return True
        except S3Error:
            return False
