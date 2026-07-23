"""Collection service."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.collection import Collection
from app.models.collection_item import CollectionItem


class CollectionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_collection(self, name: str, owner_id: str, description: Optional[str] = None) -> Collection:
        collection = Collection(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            owner_id=owner_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(collection)
        await self.db.flush()
        await self.db.refresh(collection)
        return collection

    async def list_collections(self, owner_id: Optional[str] = None) -> list:
        query = select(Collection).where(Collection.is_deleted == False)
        if owner_id:
            query = query.where(Collection.owner_id == owner_id)
        query = query.order_by(Collection.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_collection(self, collection_id: str) -> Optional[Collection]:
        result = await self.db.execute(
            select(Collection).where(Collection.id == collection_id, Collection.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def update_collection(self, collection_id: str, **kwargs) -> Optional[Collection]:
        collection = await self.get_collection(collection_id)
        if not collection:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(collection, key):
                setattr(collection, key, value)
        collection.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return collection

    async def delete_collection(self, collection_id: str) -> bool:
        collection = await self.get_collection(collection_id)
        if not collection:
            return False
        collection.is_deleted = True
        await self.db.flush()
        return True

    async def add_artwork(self, collection_id: str, artwork_id: str) -> bool:
        # Check not already in collection
        existing = await self.db.execute(
            select(CollectionItem).where(
                CollectionItem.collection_id == collection_id,
                CollectionItem.artwork_id == artwork_id,
                CollectionItem.is_deleted == False,
            )
        )
        if existing.scalar_one_or_none():
            return False

        item = CollectionItem(
            id=str(uuid.uuid4()),
            collection_id=collection_id,
            artwork_id=artwork_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(item)

        # Update count
        collection = await self.get_collection(collection_id)
        if collection:
            collection.item_count = (collection.item_count or 0) + 1

        await self.db.flush()
        return True

    async def remove_artwork(self, collection_id: str, artwork_id: str) -> bool:
        result = await self.db.execute(
            select(CollectionItem).where(
                CollectionItem.collection_id == collection_id,
                CollectionItem.artwork_id == artwork_id,
                CollectionItem.is_deleted == False,
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return False
        item.is_deleted = True

        collection = await self.get_collection(collection_id)
        if collection and collection.item_count > 0:
            collection.item_count -= 1

        await self.db.flush()
        return True
