"""Artwork preview model."""

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ArtworkPreview(BaseModel):
    __tablename__ = "artwork_previews"

    artwork_id = Column(String(36), ForeignKey("artworks.id"), nullable=False, index=True)
    preview_type = Column(String(20), nullable=False)  # thumbnail, medium, large
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    storage_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False)

    # Relationships
    artwork = relationship("Artwork", back_populates="previews")
