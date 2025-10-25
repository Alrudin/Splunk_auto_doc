"""Pydantic schemas for input API models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InputResponse(BaseModel):
    """Schema for input API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique identifier for the input")
    run_id: int = Field(description="ID of the ingestion run")
    source_path: str = Field(description="Path to source inputs.conf")
    stanza_type: str | None = Field(None, description="Input type (monitor://, tcp://, etc.)")
    index: str | None = Field(None, description="Target index")
    sourcetype: str | None = Field(None, description="Sourcetype")
    disabled: bool | None = Field(None, description="Whether input is disabled")
    kv: dict[str, Any] | None = Field(None, description="Additional key-value pairs")
    app: str | None = Field(None, description="Splunk app name")
    scope: str | None = Field(None, description="Scope (default or local)")
    layer: str | None = Field(None, description="Layer (system or app)")


class InputListResponse(BaseModel):
    """Schema for paginated list of inputs."""

    inputs: list[InputResponse]
    total: int
    page: int = 1
    per_page: int = 50
