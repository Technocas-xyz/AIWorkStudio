"""Tag endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.schemas.common import APIResponse
from app.services.tag_service import TagService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = "#3b82f6"
    tag_type: str = "manual"


class TagArtworkBody(BaseModel):
    artwork_id: str
    tag_id: str


@router.get("", response_model=APIResponse)
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TagService(db)
    tags = await service.list_tags()
    return APIResponse(data=[
        {"id": t.id, "name": t.name, "color": t.color, "tag_type": t.tag_type}
        for t in tags
    ])


@router.post("", response_model=APIResponse)
async def create_tag(
    body: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TagService(db)
    tag = await service.create_tag(name=body.name, color=body.color, tag_type=body.tag_type)
    return APIResponse(message="Tag created", data={"id": tag.id, "name": tag.name})


@router.delete("/{tag_id}", response_model=APIResponse)
async def delete_tag(
    tag_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TagService(db)
    if not await service.delete_tag(tag_id):
        raise HTTPException(status_code=404, detail="Tag not found")
    return APIResponse(message="Tag deleted")


@router.post("/assign", response_model=APIResponse)
async def assign_tag(
    body: TagArtworkBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TagService(db)
    await service.add_tag_to_artwork(body.artwork_id, body.tag_id)
    return APIResponse(message="Tag assigned")


@router.post("/remove", response_model=APIResponse)
async def remove_tag(
    body: TagArtworkBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TagService(db)
    await service.remove_tag_from_artwork(body.artwork_id, body.tag_id)
    return APIResponse(message="Tag removed")
