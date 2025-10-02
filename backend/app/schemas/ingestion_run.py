"""Pydantic schemas for ingestion run API models."""

from datetime import datetime

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


class IngestionRunListResponse(BaseModel):
    """Schema for paginated list of ingestion runs."""

    runs: list[IngestionRunResponse]
    total: int
    page: int = 1
    per_page: int = 50
