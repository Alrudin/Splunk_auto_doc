"""Pydantic schemas for props API models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PropsResponse(BaseModel):
    """Schema for props API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique identifier for the props")
    run_id: int = Field(description="ID of the ingestion run")
    target: str = Field(description="Sourcetype or source pattern")
    transforms_list: list[str] | None = Field(
        None, description="TRANSFORMS-* stanzas in order"
    )
    sedcmds: list[str] | None = Field(None, description="SEDCMD-* patterns")
    kv: dict[str, Any] | None = Field(None, description="Additional key-value pairs")


class PropsListResponse(BaseModel):
    """Schema for paginated list of props."""

    props: list[PropsResponse]
    total: int
    page: int = 1
    per_page: int = 50
