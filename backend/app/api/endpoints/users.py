"""User management endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.schemas.common import APIResponse
from app.services.user_service import UserService
from app.services.audit_service import AuditService
from app.api.deps import get_current_user, require_permission
from app.models.user import User

router = APIRouter()


@router.get("", response_model=APIResponse[UserListResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List users with pagination."""
    user_service = UserService(db)
    result = await user_service.list_users(page=page, page_size=page_size, search=search)
    return APIResponse(
        data=UserListResponse(
            items=[
                UserResponse(
                    id=u.id,
                    email=u.email,
                    username=u.username,
                    first_name=u.first_name,
                    last_name=u.last_name,
                    full_name=u.full_name,
                    is_active=u.is_active,
                    is_verified=u.is_verified,
                    role_id=u.role_id,
                    role_name=u.role.name if u.role else None,
                    avatar_url=u.avatar_url,
                    last_login=u.last_login,
                    created_at=u.created_at,
                    updated_at=u.updated_at,
                )
                for u in result["items"]
            ],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )
    )


@router.post("", response_model=APIResponse[UserResponse])
async def create_user(
    request: Request,
    body: UserCreate,
    current_user: User = Depends(require_permission("Settings.Manage")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user."""
    user_service = UserService(db)
    audit_service = AuditService(db)

    existing = await user_service.get_user_by_email(body.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = await user_service.create_user(
        email=body.email,
        username=body.username,
        password=body.password,
        first_name=body.first_name,
        last_name=body.last_name,
        role_id=str(body.role_id),
    )

    await audit_service.log(
        action="user.create",
        resource_type="user",
        user_id=current_user.id,
        resource_id=user.id,
        details={"email": user.email, "username": user.username},
        ip_address=request.client.host if request.client else None,
    )

    return APIResponse(
        message="User created successfully",
        data=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            role_id=user.role_id,
            role_name=user.role.name if user.role else None,
            avatar_url=user.avatar_url,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at,
        ),
    )


@router.put("/{user_id}", response_model=APIResponse[UserResponse])
async def update_user(
    user_id: str,
    body: UserUpdate,
    request: Request,
    current_user: User = Depends(require_permission("Settings.Manage")),
    db: AsyncSession = Depends(get_db),
):
    """Update a user."""
    user_service = UserService(db)
    audit_service = AuditService(db)

    update_data = body.model_dump(exclude_unset=True)
    if "role_id" in update_data and update_data["role_id"]:
        update_data["role_id"] = str(update_data["role_id"])

    user = await user_service.update_user(user_id, **update_data)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await audit_service.log(
        action="user.update",
        resource_type="user",
        user_id=current_user.id,
        resource_id=user.id,
        details=update_data,
        ip_address=request.client.host if request.client else None,
    )

    return APIResponse(
        message="User updated successfully",
        data=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            role_id=user.role_id,
            role_name=user.role.name if user.role else None,
            avatar_url=user.avatar_url,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at,
        ),
    )
