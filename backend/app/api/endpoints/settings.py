"""Settings endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.schemas.common import APIResponse
from app.services.audit_service import AuditService
from app.api.deps import get_current_user, require_permission
from app.models.user import User
from app.models.system_setting import SystemSetting

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all system settings."""
    result = await db.execute(select(SystemSetting).where(SystemSetting.is_deleted == False))
    settings = result.scalars().all()

    settings_dict = {}
    for s in settings:
        if s.category not in settings_dict:
            settings_dict[s.category] = {}
        settings_dict[s.category][s.key] = s.value

    return APIResponse(data=settings_dict)


@router.put("", response_model=APIResponse)
async def update_settings(
    request: Request,
    body: dict,
    current_user: User = Depends(require_permission("Settings.Manage")),
    db: AsyncSession = Depends(get_db),
):
    """Update system settings."""
    audit_service = AuditService(db)

    for key, value in body.items():
        result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = str(value)
        else:
            setting = SystemSetting(key=key, value=str(value))
            db.add(setting)

    await audit_service.log(
        action="settings.update",
        resource_type="settings",
        user_id=current_user.id,
        details=body,
        ip_address=request.client.host if request.client else None,
    )

    return APIResponse(message="Settings updated successfully")
