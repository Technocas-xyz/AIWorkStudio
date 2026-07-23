"""CollectionItem junction model."""

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class CollectionItem(BaseModel):
    __tablename__ = "collection_items"

    collection_id = Column(String(36), ForeignKey("collections.id"), nullable=False, index=True)
    artwork_id = Column(String(36), ForeignKey("artworks.id"), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)

    # Relationships
    collection = relationship("Collection", back_populates="items")
    artwork = relationship("Artwork")
