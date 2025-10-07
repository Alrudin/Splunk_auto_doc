"""Transform model for normalized Splunk transforms.conf entries."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.ingestion_run import IngestionRun


class Transform(Base):
    """Model for normalized Splunk transform configurations.

    Represents parsed transforms from transforms.conf, with key fields
    extracted and metadata about index/sourcetype writes.
    """

    __tablename__ = "transforms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="Transform name/stanza header"
    )
    dest_key: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="DEST_KEY value"
    )
    regex: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="REGEX pattern"
    )
    format: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="FORMAT template"
    )
    writes_meta_index: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True, comment="Whether transform writes to _MetaData:Index"
    )
    writes_meta_sourcetype: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        comment="Whether transform writes to _MetaData:Sourcetype",
    )
    kv: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Additional key-value pairs"
    )

    # Relationships
    ingestion_run: Mapped["IngestionRun"] = relationship(
        "IngestionRun", back_populates="transforms"
    )

    def __repr__(self) -> str:
        """String representation of Transform."""
        return (
            f"<Transform(id={self.id}, run_id={self.run_id}, "
            f"name={self.name}, dest_key={self.dest_key})>"
        )
