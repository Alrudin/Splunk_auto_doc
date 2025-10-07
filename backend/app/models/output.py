"""Output model for normalized Splunk outputs.conf entries."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.ingestion_run import IngestionRun


class Output(Base):
    """Model for normalized Splunk output configurations.

    Represents parsed output groups from outputs.conf, with server lists
    and additional properties.
    """

    __tablename__ = "outputs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    group_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Output group name"
    )
    servers: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Server list and configurations"
    )
    kv: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Additional key-value pairs"
    )

    # Relationships
    ingestion_run: Mapped["IngestionRun"] = relationship(
        "IngestionRun", back_populates="outputs"
    )

    def __repr__(self) -> str:
        """String representation of Output."""
        return (
            f"<Output(id={self.id}, run_id={self.run_id}, "
            f"group_name={self.group_name})>"
        )
