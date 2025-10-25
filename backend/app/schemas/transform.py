"""Pydantic schemas for transform API models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TransformResponse(BaseModel):
    """Schema for transform API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique identifier for the transform")
    run_id: int = Field(description="ID of the ingestion run")
    name: str = Field(description="Transform name/stanza header")
    dest_key: str | None = Field(None, description="DEST_KEY value")
    regex: str | None = Field(None, description="REGEX pattern")
    format: str | None = Field(None, description="FORMAT template")
    writes_meta_index: bool | None = Field(
        None, description="Whether transform writes to _MetaData:Index"
    )
    writes_meta_sourcetype: bool | None = Field(
        None, description="Whether transform writes to _MetaData:Sourcetype"
    )
    kv: dict[str, Any] | None = Field(None, description="Additional key-value pairs")


class TransformListResponse(BaseModel):
    """Schema for paginated list of transforms."""

    transforms: list[TransformResponse]
    total: int
    page: int = 1
    per_page: int = 50
