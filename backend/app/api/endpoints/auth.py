"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, UserMeResponse
from app.schemas.common import APIResponse
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return tokens."""
    auth_service = AuthService(db)
    audit_service = AuditService(db)

    user = await auth_service.authenticate_user(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = AuthService.create_access_token(str(user.id))
    refresh_token = AuthService.create_refresh_token(str(user.id))

    # Audit log
    await audit_service.log(
        action="login",
        resource_type="auth",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    from app.config import get_settings
    settings = get_settings()

    return APIResponse(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )
    )


@router.post("/logout", response_model=APIResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout user."""
    audit_service = AuditService(db)
    await audit_service.log(
        action="logout",
        resource_type="auth",
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse(message="Logged out successfully")


@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token."""
    auth_service = AuthService(db)
    payload = AuthService.decode_token(body.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await auth_service.get_user_by_id(payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = AuthService.create_access_token(str(user.id))
    refresh_token = AuthService.create_refresh_token(str(user.id))

    from app.config import get_settings
    settings = get_settings()

    return APIResponse(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )
    )


@router.get("/me", response_model=APIResponse[UserMeResponse])
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current authenticated user info."""
    auth_service = AuthService(db)
    permissions = await auth_service.get_user_permissions(current_user)

    return APIResponse(
        data=UserMeResponse(
            id=str(current_user.id),
            email=current_user.email,
            username=current_user.username,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            full_name=current_user.full_name,
            role=current_user.role.name if current_user.role else "unknown",
            permissions=permissions,
            avatar_url=current_user.avatar_url,
            is_active=current_user.is_active,
        )
    )
