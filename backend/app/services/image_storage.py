"""
交易图片附件校验与存储。
"""
import uuid
from pathlib import Path
from typing import Protocol

import boto3
from fastapi import HTTPException, UploadFile, status

from app.config import Settings
from app.models.transaction import TransactionImage

MAX_IMAGES_PER_TRANSACTION = 3
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png"}
JPEG_MAGIC_PREFIXES = (b"\xff\xd8\xff",)
PNG_MAGIC_PREFIX = b"\x89PNG\r\n\x1a\n"


class ObjectStorage(Protocol):
    async def save(self, key: str, data: bytes, content_type: str) -> str:
        ...

    async def delete(self, storage_path: str) -> None:
        ...


def can_add_image(current_count: int) -> bool:
    return current_count < MAX_IMAGES_PER_TRANSACTION


def detect_image_mime_type(data: bytes) -> str | None:
    if data.startswith(PNG_MAGIC_PREFIX):
        return "image/png"
    if any(data.startswith(prefix) for prefix in JPEG_MAGIC_PREFIXES):
        return "image/jpeg"
    return None


def validate_image_constraints(current_count: int, file_size_bytes: int, mime_type: str | None) -> None:
    if not can_add_image(current_count):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Maximum image limit reached")
    if file_size_bytes > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Image file is too large")
    if mime_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported image type")


async def read_upload_with_limit(upload: UploadFile) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_IMAGE_SIZE_BYTES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Image file is too large")
        chunks.append(chunk)
    data = b"".join(chunks)
    mime_type = detect_image_mime_type(data)
    validate_image_constraints(0, len(data), mime_type)
    return data


def image_storage_key(transaction_id: uuid.UUID, mime_type: str) -> str:
    extension = "png" if mime_type == "image/png" else "jpg"
    return f"transactions/{transaction_id}/{uuid.uuid4()}.{extension}"


class LocalImageStorage:
    def __init__(self, root: str) -> None:
        self.root = Path(root)

    async def save(self, key: str, data: bytes, content_type: str) -> str:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)

    async def delete(self, storage_path: str) -> None:
        path = Path(storage_path)
        try:
            path.relative_to(self.root)
        except ValueError:
            return
        try:
            path.unlink()
        except FileNotFoundError:
            return


class S3ImageStorage:
    def __init__(self, settings: Settings) -> None:
        self.bucket = settings.s3_bucket_name
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )

    async def save(self, key: str, data: bytes, content_type: str) -> str:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return f"s3://{self.bucket}/{key}"

    async def delete(self, storage_path: str) -> None:
        prefix = f"s3://{self.bucket}/"
        if not storage_path.startswith(prefix):
            return
        key = storage_path[len(prefix):]
        self.client.delete_object(Bucket=self.bucket, Key=key)


def get_image_storage(settings: Settings) -> ObjectStorage:
    if settings.storage_backend == "s3":
        return S3ImageStorage(settings)
    return LocalImageStorage(settings.local_storage_path)


async def delete_stored_images(storage: ObjectStorage, images: list[TransactionImage]) -> None:
    for image in images:
        await storage.delete(image.storage_path)
