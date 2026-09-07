from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class DocumentResponse(BaseModel):
    id: UUID
    original_filename: str
    mime_type: str
    file_size: int
    sha256_hash: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True