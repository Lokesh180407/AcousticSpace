import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, DateTime, ForeignKey, Enum, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, new_uuid


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisHistory(Base, TimestampMixin):
    __tablename__ = "analysis_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    audio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("uploaded_audio.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Denormalized owner reference for fast history lookups without a join.
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    guest_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, name="analysis_status"),
        default=AnalysisStatus.PENDING,
        nullable=False,
    )
    pipeline_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    audio: Mapped["UploadedAudio"] = relationship(back_populates="analyses")
    predictions: Mapped[List["PredictionResult"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AnalysisHistory id={self.id} audio_id={self.audio_id} status={self.status}>"
