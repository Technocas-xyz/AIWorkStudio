"""Project service."""

import math
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.project import Project


class ProjectService:
    """Handles project business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(
        self,
        name: str,
        owner_id: str,
        created_by_id: str,
        client: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Project:
        """Create a new project."""
        project = Project(
            name=name,
            client=client,
            description=description,
            owner_id=str(owner_id),
            created_by_id=str(created_by_id),
        )
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.owner))
            .where(Project.id == str(project_id), Project.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def list_projects(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> dict:
        """List projects with pagination and filters."""
        query = select(Project).options(selectinload(Project.owner)).where(Project.is_deleted == False)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                (Project.name.ilike(search_filter))
                | (Project.client.ilike(search_filter))
            )

        if status:
            query = query.where(Project.status == status)

        if owner_id:
            query = query.where(Project.owner_id == str(owner_id))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Project.created_at.desc())
        result = await self.db.execute(query)
        projects = result.scalars().all()

        return {
            "items": projects,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        }

    async def update_project(self, project_id: str, **kwargs) -> Optional[Project]:
        """Update project fields."""
        project = await self.get_project_by_id(project_id)
        if not project:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(project, key):
                setattr(project, key, value)

        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def soft_delete_project(self, project_id: str) -> bool:
        """Soft delete a project."""
        project = await self.get_project_by_id(project_id)
        if not project:
            return False
        project.is_deleted = True
        await self.db.flush()
        return True
