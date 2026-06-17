"""
交易图片附件 API 路由
"""
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db
from app.models.transaction import Transaction, TransactionImage
from app.models.user import User
from app.schemas.image import TransactionImageResponse
from app.services.auth import get_current_user
from app.services.image_storage import (
    delete_stored_images,
    detect_image_mime_type,
    get_image_storage,
    image_storage_key,
    read_upload_with_limit,
    validate_image_constraints,
)
from app.services.ledger import get_ledger_or_404, require_write_ledger

router = APIRouter(prefix="/transactions/{transaction_id}/images", tags=["images"])


async def get_transaction_with_images_or_404(
    db: AsyncSession,
    transaction_id: uuid.UUID,
) -> Transaction:
    transaction = await db.scalar(
        select(Transaction)
        .options(selectinload(Transaction.images))
        .where(Transaction.id == transaction_id)
    )
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction


@router.post("", response_model=TransactionImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_transaction_image(
    transaction_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionImage:
    transaction = await get_transaction_with_images_or_404(db, transaction_id)
    ledger = await get_ledger_or_404(db, transaction.ledger_id)
    await require_write_ledger(db, ledger, current_user)

    current_count = await db.scalar(
        select(func.count()).select_from(TransactionImage).where(TransactionImage.transaction_id == transaction_id)
    )
    data = await read_upload_with_limit(file)
    mime_type = detect_image_mime_type(data)
    validate_image_constraints(current_count or 0, len(data), mime_type)

    storage = get_image_storage(get_settings())
    storage_path = await storage.save(image_storage_key(transaction_id, mime_type or "image/jpeg"), data, mime_type or "")
    image = TransactionImage(
        transaction_id=transaction_id,
        storage_path=storage_path,
        mime_type=mime_type or "",
        file_size_bytes=len(data),
    )
    db.add(image)
    await db.flush()
    return image


@router.delete("/{image_id}")
async def delete_transaction_image(
    transaction_id: uuid.UUID,
    image_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    transaction = await get_transaction_with_images_or_404(db, transaction_id)
    ledger = await get_ledger_or_404(db, transaction.ledger_id)
    await require_write_ledger(db, ledger, current_user)
    image = await db.scalar(
        select(TransactionImage).where(
            TransactionImage.id == image_id,
            TransactionImage.transaction_id == transaction_id,
        )
    )
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    await delete_stored_images(get_image_storage(get_settings()), [image])
    await db.delete(image)
    return {"detail": "Image deleted successfully."}
