"""Pydantic schemas for output API models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OutputResponse(BaseModel):
    """Schema for output API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique identifier for the output")
    run_id: int = Field(description="ID of the ingestion run")
    group_name: str = Field(description="Output group name")
    servers: dict[str, Any] | None = Field(
        None, description="Server list and configurations"
    )
    kv: dict[str, Any] | None = Field(None, description="Additional key-value pairs")


class OutputListResponse(BaseModel):
    """Schema for paginated list of outputs."""

    outputs: list[OutputResponse]
    total: int
    page: int = 1
    per_page: int = 50
