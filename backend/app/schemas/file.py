"""Pydantic schemas for file API models."""

from pydantic import BaseModel, ConfigDict, Field


class FileBase(BaseModel):
    """Base schema for file."""

    path: str = Field(description="File path or archive filename")
    sha256: str = Field(description="SHA256 hash of file content")
    size_bytes: int = Field(description="File size in bytes")
    stored_object_key: str = Field(description="Storage reference key")


class FileResponse(FileBase):
    """Schema for file API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique identifier for the file")
    run_id: int = Field(description="ID of the associated ingestion run")
