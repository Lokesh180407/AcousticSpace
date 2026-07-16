import enum
import uuid
from typing import List, Optional

from sqlalchemy import String, Integer, Float, ForeignKey, Enum, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, new_uuid


class AudioStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadedAudio(Base, TimestampMixin):
    __tablename__ = "uploaded_audio"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)

    # Exactly one of these two should be set (enforced at the application layer).
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    guest_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    status: Mapped[AudioStatus] = mapped_column(
        Enum(AudioStatus, name="audio_status"), default=AudioStatus.UPLOADED, nullable=False
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="uploaded_audio")
    analyses: Mapped[List["AnalysisHistory"]] = relationship(
        back_populates="audio", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        owner = f"user_id={self.user_id}" if self.user_id else f"guest_id={self.guest_id}"
        return f"<UploadedAudio id={self.id} {owner} status={self.status}>"
