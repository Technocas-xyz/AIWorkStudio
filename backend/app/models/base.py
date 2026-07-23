"""Base model with common fields."""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Boolean, String
from app.database.base import Base


class BaseModel(Base):
    """Abstract base model with UUID primary key and timestamps."""

    __abstract__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
