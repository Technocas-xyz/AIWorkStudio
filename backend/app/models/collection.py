"""Collection model."""

from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Collection(BaseModel):
    __tablename__ = "collections"

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(1000), nullable=True)
    item_count = Column(Integer, default=0, nullable=False)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Relationships
    owner = relationship("User")
    items = relationship("CollectionItem", back_populates="collection")
