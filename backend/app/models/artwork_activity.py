"""Artwork activity log model."""

from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ArtworkActivity(BaseModel):
    __tablename__ = "artwork_activities"

    artwork_id = Column(String(36), ForeignKey("artworks.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)

    # Relationships
    artwork = relationship("Artwork", back_populates="activities")
    user = relationship("User")
