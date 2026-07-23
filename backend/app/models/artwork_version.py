"""Artwork version model."""

from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ArtworkVersion(BaseModel):
    __tablename__ = "artwork_versions"

    artwork_id = Column(String(36), ForeignKey("artworks.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    version_type = Column(String(50), default="upload", nullable=False)  # upload, edit, restore, master, production, export
    filename = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    checksum = Column(String(64), nullable=False)
    storage_bucket = Column(String(100), nullable=False)
    storage_path = Column(String(1000), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Relationships
    artwork = relationship("Artwork", back_populates="versions")
    created_by = relationship("User")
