import uuid

from sqlalchemy import String, Float, ForeignKey, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, new_uuid


class PredictionResult(Base, TimestampMixin):
    __tablename__ = "prediction_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("analysis_history.id", ondelete="CASCADE"), nullable=False, index=True
    )

    label: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "real" | "fake"
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Full raw model output (per-branch scores, RIR features, etc.) for auditability.
    raw_output: Mapped[dict] = mapped_column(JSON, nullable=True)

    analysis: Mapped["AnalysisHistory"] = relationship(back_populates="predictions")

    def __repr__(self) -> str:
        return f"<PredictionResult id={self.id} label={self.label} score={self.confidence_score}>"
