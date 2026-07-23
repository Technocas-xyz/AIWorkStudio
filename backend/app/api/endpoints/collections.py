"""Collection endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.schemas.common import APIResponse
from app.services.collection_service import CollectionService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CollectionItemAdd(BaseModel):
    artwork_id: str


@router.get("", response_model=APIResponse)
async def list_collections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CollectionService(db)
    collections = await service.list_collections()
    return APIResponse(data=[
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "item_count": c.item_count,
            "owner_id": c.owner_id,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in collections
    ])


@router.post("", response_model=APIResponse)
async def create_collection(
    body: CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CollectionService(db)
    collection = await service.create_collection(
        name=body.name, description=body.description, owner_id=current_user.id
    )
    return APIResponse(message="Collection created", data={
        "id": collection.id, "name": collection.name
    })


@router.put("/{collection_id}", response_model=APIResponse)
async def update_collection(
    collection_id: str,
    body: CollectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CollectionService(db)
    update_data = body.model_dump(exclude_unset=True)
    collection = await service.update_collection(collection_id, **update_data)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return APIResponse(message="Collection updated")


@router.delete("/{collection_id}", response_model=APIResponse)
async def delete_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CollectionService(db)
    if not await service.delete_collection(collection_id):
        raise HTTPException(status_code=404, detail="Collection not found")
    return APIResponse(message="Collection deleted")


@router.post("/{collection_id}/artworks", response_model=APIResponse)
async def add_artwork_to_collection(
    collection_id: str,
    body: CollectionItemAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CollectionService(db)
    added = await service.add_artwork(collection_id, body.artwork_id)
    if not added:
        return APIResponse(message="Artwork already in collection", code=409)
    return APIResponse(message="Artwork added to collection")


@router.delete("/{collection_id}/artworks/{artwork_id}", response_model=APIResponse)
async def remove_artwork_from_collection(
    collection_id: str,
    artwork_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CollectionService(db)
    if not await service.remove_artwork(collection_id, artwork_id):
        raise HTTPException(status_code=404, detail="Item not found")
    return APIResponse(message="Artwork removed from collection")
