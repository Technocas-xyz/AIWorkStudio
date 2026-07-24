"""Tag service."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.tag import Tag
from app.models.artwork_tag import ArtworkTag


class TagService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tag(self, name: str, color: str = "#3b82f6", tag_type: str = "manual") -> Tag:
        # Check if exists
        existing = await self.db.execute(select(Tag).where(Tag.name == name))
        tag = existing.scalar_one_or_none()
        if tag:
            return tag

        tag = Tag(
            id=str(uuid.uuid4()),
            name=name,
            color=color,
            tag_type=tag_type,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(tag)
        await self.db.flush()
        return tag

    async def list_tags(self) -> list:
        result = await self.db.execute(
            select(Tag).where(Tag.is_deleted == False).order_by(Tag.name)
        )
        return list(result.scalars().all())

    async def delete_tag(self, tag_id: str) -> bool:
        result = await self.db.execute(select(Tag).where(Tag.id == tag_id))
        tag = result.scalar_one_or_none()
        if not tag:
            return False
        tag.is_deleted = True
        await self.db.flush()
        return True

    async def add_tag_to_artwork(self, artwork_id: str, tag_id: str) -> bool:
        existing = await self.db.execute(
            select(ArtworkTag).where(
                ArtworkTag.artwork_id == artwork_id,
                ArtworkTag.tag_id == tag_id,
                ArtworkTag.is_deleted == False,
            )
        )
        if existing.scalar_one_or_none():
            return False

        at = ArtworkTag(
            id=str(uuid.uuid4()),
            artwork_id=artwork_id,
            tag_id=tag_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(at)
        await self.db.flush()
        return True

    async def remove_tag_from_artwork(self, artwork_id: str, tag_id: str) -> bool:
        result = await self.db.execute(
            select(ArtworkTag).where(
                ArtworkTag.artwork_id == artwork_id,
                ArtworkTag.tag_id == tag_id,
                ArtworkTag.is_deleted == False,
            )
        )
        at = result.scalar_one_or_none()
        if not at:
            return False
        at.is_deleted = True
        await self.db.flush()
        return True

    async def get_artwork_tags(self, artwork_id: str) -> list:
        result = await self.db.execute(
            select(Tag)
            .join(ArtworkTag, ArtworkTag.tag_id == Tag.id)
            .where(ArtworkTag.artwork_id == artwork_id, ArtworkTag.is_deleted == False)
        )
        return list(result.scalars().all())
