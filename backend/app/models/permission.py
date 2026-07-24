"""Permission model."""

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Permission(BaseModel):
    __tablename__ = "permissions"

    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    module = Column(String(50), nullable=False, index=True)

    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission")
