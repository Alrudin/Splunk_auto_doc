"""Stanza model for normalized Splunk configuration stanzas."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import JSONB

if TYPE_CHECKING:
    from app.models.file import File
    from app.models.ingestion_run import IngestionRun


class Stanza(Base):
    """Model for parsed configuration stanzas.

    Represents a stanza parsed from a Splunk .conf file, with full
    provenance metadata (run, file, app, scope, layer) and raw key-value
    pairs stored as JSONB.
    """

    __tablename__ = "stanzas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    file_id: Mapped[int | None] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"), nullable=True
    )
    conf_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type: inputs|props|transforms|indexes|outputs|serverclasses|other",
    )
    name: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="Stanza header/name"
    )
    app: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scope: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="default or local"
    )
    layer: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="system or app"
    )
    order_in_file: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_path: Mapped[str] = mapped_column(
        String(1024), nullable=False, comment="Full path to source .conf file"
    )
    raw_kv: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Raw key-value pairs from stanza"
    )

    # Relationships
    ingestion_run: Mapped["IngestionRun"] = relationship(
        "IngestionRun", back_populates="stanzas"
    )
    file: Mapped["File | None"] = relationship("File", back_populates="stanzas")

    def __repr__(self) -> str:
        """String representation of Stanza."""
        return (
            f"<Stanza(id={self.id}, run_id={self.run_id}, "
            f"conf_type={self.conf_type}, name={self.name})>"
        )
