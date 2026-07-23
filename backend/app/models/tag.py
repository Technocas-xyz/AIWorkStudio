"""Tag model."""

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Tag(BaseModel):
    __tablename__ = "tags"

    name = Column(String(100), unique=True, nullable=False, index=True)
    color = Column(String(7), default="#3b82f6", nullable=False)
    tag_type = Column(String(30), default="manual", nullable=False)  # manual, system, project, client, ai

    # Relationships
    artwork_tags = relationship("ArtworkTag", back_populates="tag")
