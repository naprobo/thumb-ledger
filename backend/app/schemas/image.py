"""
交易图片附件 Schema
"""
import uuid
from datetime import datetime

from pydantic import BaseModel


class TransactionImageResponse(BaseModel):
    id: uuid.UUID
    transaction_id: uuid.UUID
    storage_path: str
    mime_type: str
    file_size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}

