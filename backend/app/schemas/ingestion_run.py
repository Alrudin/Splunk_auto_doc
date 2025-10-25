"""Pydantic schemas for ingestion run API models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.ingestion_run import IngestionStatus, IngestionType


class IngestionRunBase(BaseModel):
    """Base schema for ingestion run."""

    type: IngestionType = Field(description="Type of configuration upload")
    label: str | None = Field(None, description="Optional human-readable label")
    notes: str | None = Field(None, description="Optional notes about this run")


class IngestionRunCreate(IngestionRunBase):
    """Schema for creating an ingestion run."""

    pass


class IngestionRunResponse(IngestionRunBase):
    """Schema for ingestion run API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique identifier for the ingestion run")
    created_at: datetime = Field(description="Timestamp when the run was created")
    status: IngestionStatus = Field(description="Current status of the ingestion run")
    task_id: str | None = Field(None, description="Celery task ID for async processing")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    error_message: str | None = Field(None, description="Error message if failed")
    error_traceback: str | None = Field(
        None, description="Full error traceback if failed"
    )
    last_heartbeat: datetime | None = Field(
        None, description="Last heartbeat timestamp"
    )
    started_at: datetime | None = Field(None, description="Task start timestamp")
    completed_at: datetime | None = Field(None, description="Task completion timestamp")
    metrics: dict[str, Any] | None = Field(None, description="Task execution metrics")


class IngestionRunListResponse(BaseModel):
    """Schema for paginated list of ingestion runs."""

    runs: list[IngestionRunResponse]
    total: int
    page: int = 1
    per_page: int = 50


class IngestionRunStatusResponse(BaseModel):
    """Schema for run status API response."""

    run_id: int = Field(description="Unique identifier for the ingestion run")
    status: IngestionStatus = Field(description="Current status of the ingestion run")
    error_message: str | None = Field(None, description="Error message if failed")
    summary: dict[str, Any] | None = Field(
        None,
        description="Summary counts: files_parsed, stanzas_created, typed_projections, etc.",
    )


class IngestionRunStatusUpdate(BaseModel):
    """Schema for updating run status (admin/debug only)."""

    status: IngestionStatus = Field(description="New status to set")
    error_message: str | None = Field(None, description="Optional error message")
