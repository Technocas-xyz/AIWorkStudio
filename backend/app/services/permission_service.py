"""Permission service for dynamic RBAC."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


class PermissionService:
    """Handles permission management and checking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def user_has_permission(self, role_id: str, permission_code: str) -> bool:
        """Check if a role has a specific permission."""
        result = await self.db.execute(
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(
                RolePermission.role_id == str(role_id),
                Permission.code == permission_code,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_role_permissions(self, role_id: str) -> list[str]:
        """Get all permission codes for a role."""
        result = await self.db.execute(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == str(role_id))
        )
        return [row[0] for row in result.all()]
