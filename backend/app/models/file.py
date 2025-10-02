"""File model for tracking uploaded files in ingestion runs."""

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.ingestion_run import IngestionRun


class File(Base):
    """Model for tracking files uploaded in an ingestion run.

    For Milestone 1, this represents the uploaded archive file.
    Future milestones may expand to track individual extracted files.
    """

    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    path: Mapped[str] = mapped_column(
        String(1024), nullable=False, comment="Archive filename (M1) or file path"
    )
    sha256: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="SHA256 hash of file content"
    )
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    stored_object_key: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="Reference to blob storage location"
    )

    # Relationships
    ingestion_run: Mapped["IngestionRun"] = relationship(
        "IngestionRun", back_populates="files"
    )

    def __repr__(self) -> str:
        """String representation of File."""
        return (
            f"<File(id={self.id}, run_id={self.run_id}, "
            f"path={self.path}, size={self.size_bytes})>"
        )
