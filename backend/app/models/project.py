"""Project model."""

from sqlalchemy import Column, String, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class ProductionStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    COMPLETED = "completed"


class Project(BaseModel):
    __tablename__ = "projects"

    name = Column(String(200), nullable=False)
    client = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="active", nullable=False)
    production_status = Column(String(20), default="not_started", nullable=False)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    artwork_count = Column(Integer, default=0, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="projects_owned", foreign_keys=[owner_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    members = relationship("ProjectMember", back_populates="project")
    files = relationship("StorageFile", back_populates="project")
