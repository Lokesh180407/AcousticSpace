import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.audio import AudioStatus


class UploadedAudioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    guest_id: Optional[str]
    original_filename: str
    content_type: str
    file_size_bytes: int
    status: AudioStatus
    created_at: datetime


class UploadResponse(BaseModel):
    audio: UploadedAudioRead
    guest_id: Optional[str] = None
    message: str = "Upload received"
