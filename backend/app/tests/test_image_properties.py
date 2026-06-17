"""
图片附件属性测试（Properties 24, 25）
"""
from pathlib import Path

import pytest
from fastapi import HTTPException
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import inspect

from app.models.transaction import Transaction, TransactionImage
from app.services.image_storage import (
    MAX_IMAGE_SIZE_BYTES,
    MAX_IMAGES_PER_TRANSACTION,
    LocalImageStorage,
    can_add_image,
    delete_stored_images,
    detect_image_mime_type,
    validate_image_constraints,
)


@given(current_count=st.integers(min_value=0, max_value=10))
@settings(max_examples=50)
def test_property_24_image_count_limit(current_count: int) -> None:
    assert can_add_image(current_count) is (current_count < MAX_IMAGES_PER_TRANSACTION)


def test_property_24_rejects_fourth_image_oversized_and_unsupported_type() -> None:
    with pytest.raises(HTTPException):
        validate_image_constraints(MAX_IMAGES_PER_TRANSACTION, 1024, "image/png")

    with pytest.raises(HTTPException):
        validate_image_constraints(0, MAX_IMAGE_SIZE_BYTES + 1, "image/png")

    with pytest.raises(HTTPException):
        validate_image_constraints(0, 1024, "image/gif")


def test_property_24_detects_jpeg_and_png_by_magic_bytes() -> None:
    assert detect_image_mime_type(b"\xff\xd8\xff\xe0data") == "image/jpeg"
    assert detect_image_mime_type(b"\x89PNG\r\n\x1a\ndata") == "image/png"
    assert detect_image_mime_type(b"not an image") is None


@pytest.mark.asyncio
async def test_property_25_local_storage_delete_removes_image_file(tmp_path: Path) -> None:
    storage = LocalImageStorage(str(tmp_path))
    storage_path = await storage.save("transactions/t1/image.png", b"\x89PNG\r\n\x1a\ndata", "image/png")
    assert Path(storage_path).exists()

    image = TransactionImage(storage_path=storage_path, mime_type="image/png", file_size_bytes=12)
    await delete_stored_images(storage, [image])

    assert not Path(storage_path).exists()


def test_property_25_transaction_delete_cascades_image_records() -> None:
    relationships = inspect(Transaction).relationships

    assert "delete-orphan" in relationships["images"].cascade

