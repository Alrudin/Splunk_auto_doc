"""Props model for normalized Splunk props.conf entries."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import ARRAY, JSONB

if TYPE_CHECKING:
    from app.models.ingestion_run import IngestionRun


class Props(Base):
    """Model for normalized Splunk props configurations.

    Represents parsed props from props.conf, with transforms and sedcmds
    extracted into arrays and additional properties in JSONB.
    """

    __tablename__ = "props"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    target: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="Sourcetype or source pattern"
    )
    transforms_list: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(255)),
        nullable=True,
        comment="TRANSFORMS-* stanzas in order",
    )
    sedcmds: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(255)),
        nullable=True,
        comment="SEDCMD-* patterns",
    )
    kv: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Additional key-value pairs"
    )

    # Relationships
    ingestion_run: Mapped["IngestionRun"] = relationship(
        "IngestionRun", back_populates="props"
    )

    def __repr__(self) -> str:
        """String representation of Props."""
        return f"<Props(id={self.id}, run_id={self.run_id}, " f"target={self.target})>"
