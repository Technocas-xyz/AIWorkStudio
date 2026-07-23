"""User service."""

import math
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user import User
from app.services.auth_service import AuthService


class UserService:
    """Handles user business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(
        self,
        email: str,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        role_id: str,
    ) -> User:
        """Create a new user."""
        hashed_password = AuthService.hash_password(password)
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role_id=str(role_id),
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == str(user_id), User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def list_users(
        self, page: int = 1, page_size: int = 20, search: Optional[str] = None
    ) -> dict:
        """List users with pagination."""
        query = select(User).where(User.is_deleted == False)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                (User.email.ilike(search_filter))
                | (User.username.ilike(search_filter))
                | (User.first_name.ilike(search_filter))
                | (User.last_name.ilike(search_filter))
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())
        result = await self.db.execute(query)
        users = result.scalars().all()

        return {
            "items": users,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        }

    async def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user fields."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)

        await self.db.flush()
        await self.db.refresh(user)
        return user
