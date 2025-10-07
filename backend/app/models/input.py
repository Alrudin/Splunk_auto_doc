"""Input model for normalized Splunk inputs.conf entries."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import JSONB

if TYPE_CHECKING:
    from app.models.ingestion_run import IngestionRun


class Input(Base):
    """Model for normalized Splunk input configurations.

    Represents parsed inputs from inputs.conf, with common fields extracted
    and additional properties stored in JSONB.
    """

    __tablename__ = "inputs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    source_path: Mapped[str] = mapped_column(
        String(1024), nullable=False, comment="Path to source inputs.conf"
    )
    stanza_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Type: monitor://, tcp://, udp://, script://, WinEventLog://, etc.",
    )
    index: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sourcetype: Mapped[str | None] = mapped_column(String(255), nullable=True)
    disabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    kv: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Additional key-value pairs"
    )
    app: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scope: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="default or local"
    )
    layer: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="system or app"
    )

    # Relationships
    ingestion_run: Mapped["IngestionRun"] = relationship(
        "IngestionRun", back_populates="inputs"
    )

    def __repr__(self) -> str:
        """String representation of Input."""
        return (
            f"<Input(id={self.id}, run_id={self.run_id}, "
            f"stanza_type={self.stanza_type}, index={self.index})>"
        )
