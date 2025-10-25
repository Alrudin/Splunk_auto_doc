"""Pydantic schemas for index API models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IndexResponse(BaseModel):
    """Schema for index API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique identifier for the index")
    run_id: int = Field(description="ID of the ingestion run")
    name: str = Field(description="Index name")
    kv: dict[str, Any] | None = Field(
        None, description="Index configuration key-value pairs"
    )


class IndexListResponse(BaseModel):
    """Schema for paginated list of indexes."""

    indexes: list[IndexResponse]
    total: int
    page: int = 1
    per_page: int = 50
