"""Index model for normalized Splunk indexes.conf entries."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.ingestion_run import IngestionRun


class Index(Base):
    """Model for normalized Splunk index configurations.

    Represents parsed indexes from indexes.conf.
    """

    __tablename__ = "indexes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Index name"
    )
    kv: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Index configuration key-value pairs"
    )

    # Relationships
    ingestion_run: Mapped["IngestionRun"] = relationship(
        "IngestionRun", back_populates="indexes"
    )

    def __repr__(self) -> str:
        """String representation of Index."""
        return f"<Index(id={self.id}, run_id={self.run_id}, name={self.name})>"
