"""Dashboard endpoints."""

import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.schemas.common import APIResponse
from app.api.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.storage_file import StorageFile
from app.models.audit_log import AuditLog

router = APIRouter()


@router.get("/stats", response_model=APIResponse)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics."""
    total_projects = await db.execute(
        select(func.count(Project.id)).where(Project.is_deleted == False)
    )
    active_projects = await db.execute(
        select(func.count(Project.id)).where(
            Project.is_deleted == False, Project.status == "active"
        )
    )
    completed_projects = await db.execute(
        select(func.count(Project.id)).where(
            Project.is_deleted == False, Project.status == "completed"
        )
    )
    storage_usage = await db.execute(
        select(func.coalesce(func.sum(StorageFile.file_size), 0)).where(
            StorageFile.is_deleted == False
        )
    )
    total_users = await db.execute(
        select(func.count(User.id)).where(User.is_deleted == False)
    )

    return APIResponse(
        data={
            "total_projects": total_projects.scalar() or 0,
            "active_projects": active_projects.scalar() or 0,
            "completed_projects": completed_projects.scalar() or 0,
            "pending_analysis": 0,
            "pending_generation": 0,
            "pending_qa": 0,
            "storage_usage_bytes": storage_usage.scalar() or 0,
            "ai_credits": 1000,
            "total_users": total_users.scalar() or 0,
        }
    )


@router.get("/recent-activity", response_model=APIResponse)
async def get_recent_activity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent activity for the dashboard."""
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.is_deleted == False)
        .order_by(AuditLog.created_at.desc())
        .limit(20)
    )
    logs = result.scalars().all()

    activities = []
    for log in logs:
        details = None
        if log.details:
            try:
                details = json.loads(log.details)
            except (json.JSONDecodeError, TypeError):
                details = None

        activities.append({
            "id": str(log.id),
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "user_id": log.user_id,
            "details": details,
            "created_at": log.created_at.isoformat(),
        })

    return APIResponse(data=activities)
