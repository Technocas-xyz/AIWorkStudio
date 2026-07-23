"""Artwork-Tag junction model."""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ArtworkTag(BaseModel):
    __tablename__ = "artwork_tags"

    artwork_id = Column(String(36), ForeignKey("artworks.id"), nullable=False, index=True)
    tag_id = Column(String(36), ForeignKey("tags.id"), nullable=False, index=True)

    # Relationships
    artwork = relationship("Artwork", back_populates="tags")
    tag = relationship("Tag", back_populates="artwork_tags")
