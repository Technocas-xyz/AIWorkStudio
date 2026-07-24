"""Project schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    client: Optional[str] = Field(None, max_length=200, description="Client name")
    description: Optional[str] = Field(None, description="Project description")


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    client: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None
    production_status: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    client: Optional[str] = None
    description: Optional[str] = None
    status: str
    production_status: str
    owner_id: str
    owner_name: Optional[str] = None
    created_by_id: str
    artwork_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
