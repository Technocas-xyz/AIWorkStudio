"""Artwork model - core DAM entity."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, BigInteger, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Artwork(BaseModel):
    __tablename__ = "artworks"

    # Identity
    artwork_id = Column(String(20), unique=True, nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    extension = Column(String(20), nullable=False, index=True)
    mime_type = Column(String(100), nullable=False)

    # Dimensions
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    resolution_dpi = Column(Integer, nullable=True)

    # Technical
    color_space = Column(String(50), nullable=True)
    bit_depth = Column(Integer, nullable=True)
    has_transparency = Column(Boolean, default=False, nullable=False)
    has_alpha_channel = Column(Boolean, default=False, nullable=False)
    orientation = Column(String(20), nullable=True)

    # Storage
    file_size = Column(BigInteger, nullable=False)
    checksum = Column(String(64), nullable=False, index=True)
    storage_bucket = Column(String(100), nullable=False)
    storage_path = Column(String(1000), nullable=False)

    # Status
    status = Column(String(30), default="active", nullable=False, index=True)
    processing_status = Column(String(30), default="completed", nullable=False)
    current_version = Column(Integer, default=1, nullable=False)

    # Relations
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    uploaded_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Flags
    is_favorite = Column(Boolean, default=False, nullable=False)

    # Relationships
    project = relationship("Project", backref="artworks")
    owner = relationship("User", foreign_keys=[owner_id])
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])
    versions = relationship("ArtworkVersion", back_populates="artwork", order_by="ArtworkVersion.version_number")
    tags = relationship("ArtworkTag", back_populates="artwork")
    previews = relationship("ArtworkPreview", back_populates="artwork")
    activities = relationship("ArtworkActivity", back_populates="artwork", order_by="ArtworkActivity.created_at.desc()")
    metadata_entries = relationship("ArtworkMetadata", back_populates="artwork")
