"""StorageFile model."""

from sqlalchemy import Column, String, BigInteger, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class StorageFile(BaseModel):
    __tablename__ = "storage_files"

    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    bucket = Column(String(100), nullable=False)
    storage_path = Column(String(1000), nullable=False)
    checksum = Column(String(64), nullable=False)
    version = Column(String(20), default="1.0", nullable=False)
    metadata_json = Column(Text, nullable=True)  # JSON as text for SQLite compat
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    uploaded_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="files")
    uploaded_by = relationship("User")
