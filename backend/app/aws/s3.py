"""
ResQNet — AWS S3 Client
Real S3 with local filesystem mock for development.
Switch via USE_S3_MOCK=true/false in .env
"""
from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from app.config import settings

logger = logging.getLogger("resqnet.aws.s3")


class S3Client:
    def __init__(self):
        self._mock = settings.use_s3_mock
        if not self._mock:
            import boto3
            self._client = boto3.client(
                "s3",
                region_name=settings.s3_region,
                aws_access_key_id=settings.aws_access_key_id or None,
                aws_secret_access_key=settings.aws_secret_access_key or None,
            )
        else:
            Path(settings.local_upload_dir).mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file_bytes: bytes,
        original_filename: str,
        content_type: str,
    ) -> str:
        """Upload a file and return the S3 key (or local path key)."""
        ext = Path(original_filename).suffix.lower()
        key = f"evidence/{uuid.uuid4()}{ext}"

        if self._mock:
            local_path = Path(settings.local_upload_dir) / key.replace("/", "_")
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(file_bytes)
            logger.info(f"[MOCK S3] Saved {len(file_bytes)} bytes to {local_path}")
        else:
            import asyncio
            loop = asyncio.get_event_loop()
            import io
            await loop.run_in_executor(
                None,
                lambda: self._client.upload_fileobj(
                    io.BytesIO(file_bytes),
                    settings.s3_bucket_name,
                    key,
                    ExtraArgs={"ContentType": content_type},
                )
            )
            logger.info(f"[S3] Uploaded to s3://{settings.s3_bucket_name}/{key}")
        return key

    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL (or local file URL in mock mode)."""
        if self._mock:
            return f"/api/evidence/file/{key.replace('/', '_')}"
        import asyncio
        loop = asyncio.get_event_loop()
        url = await loop.run_in_executor(
            None,
            lambda: self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.s3_bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
        )
        return url

    async def delete_file(self, key: str) -> bool:
        if self._mock:
            local_path = Path(settings.local_upload_dir) / key.replace("/", "_")
            if local_path.exists():
                local_path.unlink()
            return True
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._client.delete_object(Bucket=settings.s3_bucket_name, Key=key)
        )
        return True


# Singleton
_s3_client: S3Client | None = None


def get_s3() -> S3Client:
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client
