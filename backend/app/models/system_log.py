import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, Enum, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import new_uuid


class LogLevel(str, enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SystemLog(Base):
    """Application/infra-level logs (background job failures, startup errors, etc.)."""

    __tablename__ = "system_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    level: Mapped[LogLevel] = mapped_column(
        Enum(LogLevel, name="log_level"), default=LogLevel.INFO, nullable=False
    )
    module: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<SystemLog id={self.id} level={self.level}>"
