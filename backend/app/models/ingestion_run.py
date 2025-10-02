"""Ingestion run model for tracking uploaded configuration bundles."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.file import File


class IngestionType(str, enum.Enum):
    """Types of ingestion uploads."""

    DS_ETC = "ds_etc"  # Deployment server etc directory
    INSTANCE_ETC = "instance_etc"  # Instance etc directory
    APP_BUNDLE = "app_bundle"  # Single app bundle
    SINGLE_CONF = "single_conf"  # Individual conf file


class IngestionStatus(str, enum.Enum):
    """Status of an ingestion run."""

    PENDING = "pending"  # Run created, file upload in progress
    STORED = "stored"  # File stored successfully
    FAILED = "failed"  # Upload or storage failed
    COMPLETE = "complete"  # Fully processed (future milestone)


class IngestionRun(Base):
    """Model for tracking ingestion runs.

    An ingestion run represents a single upload of Splunk configuration
    files (tar/zip archive). Each run tracks the uploaded files and
    their processing status.
    """

    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    type: Mapped[IngestionType] = mapped_column(
        Enum(IngestionType, native_enum=False, length=50), nullable=False
    )
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[IngestionStatus] = mapped_column(
        Enum(IngestionStatus, native_enum=False, length=50),
        default=IngestionStatus.PENDING,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    files: Mapped[list["File"]] = relationship(
        "File", back_populates="ingestion_run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of IngestionRun."""
        return (
            f"<IngestionRun(id={self.id}, type={self.type.value}, "
            f"status={self.status.value}, created_at={self.created_at})>"
        )
