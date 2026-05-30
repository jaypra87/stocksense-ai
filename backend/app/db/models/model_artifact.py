from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ModelArtifact(Base):
    """One trained model bundle (per version, per horizon). Maps a model_version
    to the joblib file on disk and records its evaluation metrics."""

    __tablename__ = "model_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_version: Mapped[str] = mapped_column(String(50), index=True)
    horizon: Mapped[str] = mapped_column(String(10), index=True)
    path: Mapped[str] = mapped_column(String(500))
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    metrics_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    feature_list_json: Mapped[list] = mapped_column(JSONB, default=list)
    # Exactly one artifact per horizon should be active at a time.
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
