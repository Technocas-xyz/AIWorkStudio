"""Artwork metadata - extensible key-value metadata storage."""

from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ArtworkMetadata(BaseModel):
    __tablename__ = "artwork_metadata"

    artwork_id = Column(String(36), ForeignKey("artworks.id"), nullable=False, index=True)
    key = Column(String(100), nullable=False, index=True)
    value = Column(Text, nullable=True)
    category = Column(String(50), default="general", nullable=False)

    # Relationships
    artwork = relationship("Artwork", back_populates="metadata_entries")
