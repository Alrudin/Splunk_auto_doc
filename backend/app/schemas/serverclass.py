"""Pydantic schemas for serverclass API models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ServerclassResponse(BaseModel):
    """Schema for serverclass API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique identifier for the serverclass")
    run_id: int = Field(description="ID of the ingestion run")
    name: str = Field(description="Serverclass name")
    whitelist: dict[str, Any] | None = Field(None, description="Whitelist patterns")
    blacklist: dict[str, Any] | None = Field(None, description="Blacklist patterns")
    app_assignments: dict[str, Any] | None = Field(
        None, description="App assignments for this serverclass"
    )
    kv: dict[str, Any] | None = Field(None, description="Additional key-value pairs")
    app: str | None = Field(None, description="Splunk app name")
    scope: str | None = Field(None, description="Scope (default or local)")
    layer: str | None = Field(None, description="Layer (system or app)")


class ServerclassListResponse(BaseModel):
    """Schema for paginated list of serverclasses."""

    serverclasses: list[ServerclassResponse]
    total: int
    page: int = 1
    per_page: int = 50
