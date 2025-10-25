"""Ingestion run model for tracking uploaded configuration bundles."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.file import File
    from app.models.index import Index
    from app.models.input import Input
    from app.models.output import Output
    from app.models.props import Props
    from app.models.serverclass import Serverclass
    from app.models.stanza import Stanza
    from app.models.transform import Transform


class IngestionType(str, enum.Enum):
    """Types of ingestion uploads."""

    DS_ETC = "ds_etc"  # Deployment server etc directory
    INSTANCE_ETC = "instance_etc"  # Instance etc directory
    APP_BUNDLE = "app_bundle"  # Single app bundle
    SINGLE_CONF = "single_conf"  # Individual conf file


class IngestionStatus(str, enum.Enum):
    """Status of an ingestion run.
    
    Lifecycle: PENDING → STORED → PARSING → NORMALIZED → COMPLETE
                                                ↓
                                             FAILED
    """

    PENDING = "pending"  # Run created, file upload in progress
    STORED = "stored"  # File stored successfully
    PARSING = "parsing"  # Parsing job enqueued or in progress
    NORMALIZED = "normalized"  # Stanzas parsed and typed projections created
    FAILED = "failed"  # Upload, storage, or parsing failed
    COMPLETE = "complete"  # Fully processed


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

    # Retry and error tracking fields
    task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_heartbeat: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    files: Mapped[list["File"]] = relationship(
        "File", back_populates="ingestion_run", cascade="all, delete-orphan"
    )
    stanzas: Mapped[list["Stanza"]] = relationship(
        "Stanza", back_populates="ingestion_run", cascade="all, delete-orphan"
    )
    inputs: Mapped[list["Input"]] = relationship(
        "Input", back_populates="ingestion_run", cascade="all, delete-orphan"
    )
    props: Mapped[list["Props"]] = relationship(
        "Props", back_populates="ingestion_run", cascade="all, delete-orphan"
    )
    transforms: Mapped[list["Transform"]] = relationship(
        "Transform", back_populates="ingestion_run", cascade="all, delete-orphan"
    )
    indexes: Mapped[list["Index"]] = relationship(
        "Index", back_populates="ingestion_run", cascade="all, delete-orphan"
    )
    outputs: Mapped[list["Output"]] = relationship(
        "Output", back_populates="ingestion_run", cascade="all, delete-orphan"
    )
    serverclasses: Mapped[list["Serverclass"]] = relationship(
        "Serverclass", back_populates="ingestion_run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of IngestionRun."""
        return (
            f"<IngestionRun(id={self.id}, type={self.type.value}, "
            f"status={self.status.value}, created_at={self.created_at})>"
        )
