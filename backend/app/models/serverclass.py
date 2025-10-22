"""Serverclass model for normalized Splunk serverclass.conf entries."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import JSONB

if TYPE_CHECKING:
    from app.models.ingestion_run import IngestionRun


class Serverclass(Base):
    """Model for normalized Splunk serverclass configurations.

    Represents parsed serverclasses from serverclass.conf, with whitelist,
    blacklist, and app assignments.
    """

    __tablename__ = "serverclasses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Serverclass name"
    )
    whitelist: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Whitelist patterns"
    )
    blacklist: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Blacklist patterns"
    )
    app_assignments: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="App assignments for this serverclass"
    )
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
        "IngestionRun", back_populates="serverclasses"
    )

    def __repr__(self) -> str:
        """String representation of Serverclass."""
        return f"<Serverclass(id={self.id}, run_id={self.run_id}, name={self.name})>"
