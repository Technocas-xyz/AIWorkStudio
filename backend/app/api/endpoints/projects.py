"""Project endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from app.schemas.common import APIResponse
from app.services.project_service import ProjectService
from app.services.audit_service import AuditService
from app.api.deps import get_current_user, require_permission
from app.models.user import User

router = APIRouter()


@router.get("", response_model=APIResponse[ProjectListResponse])
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List projects with pagination and filters."""
    project_service = ProjectService(db)
    result = await project_service.list_projects(
        page=page, page_size=page_size, search=search, status=status
    )
    return APIResponse(
        data=ProjectListResponse(
            items=[
                ProjectResponse(
                    id=p.id,
                    name=p.name,
                    client=p.client,
                    description=p.description,
                    status=p.status or "active",
                    production_status=p.production_status or "not_started",
                    owner_id=p.owner_id,
                    owner_name=p.owner.full_name if p.owner else None,
                    created_by_id=p.created_by_id,
                    artwork_count=p.artwork_count,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
                for p in result["items"]
            ],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )
    )


@router.post("", response_model=APIResponse[ProjectResponse])
async def create_project(
    request: Request,
    body: ProjectCreate,
    current_user: User = Depends(require_permission("Project.Create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    project_service = ProjectService(db)
    audit_service = AuditService(db)

    project = await project_service.create_project(
        name=body.name,
        client=body.client,
        description=body.description,
        owner_id=current_user.id,
        created_by_id=current_user.id,
    )

    await audit_service.log(
        action="project.create",
        resource_type="project",
        user_id=current_user.id,
        resource_id=project.id,
        details={"name": project.name},
        ip_address=request.client.host if request.client else None,
    )

    return APIResponse(
        message="Project created successfully",
        data=ProjectResponse(
            id=project.id,
            name=project.name,
            client=project.client,
            description=project.description,
            status=project.status or "active",
            production_status=project.production_status or "not_started",
            owner_id=project.owner_id,
            owner_name=current_user.full_name,
            created_by_id=project.created_by_id,
            artwork_count=project.artwork_count,
            created_at=project.created_at,
            updated_at=project.updated_at,
        ),
    )


@router.put("/{project_id}", response_model=APIResponse[ProjectResponse])
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    request: Request,
    current_user: User = Depends(require_permission("Project.Create")),
    db: AsyncSession = Depends(get_db),
):
    """Update a project."""
    project_service = ProjectService(db)
    audit_service = AuditService(db)

    update_data = body.model_dump(exclude_unset=True)
    project = await project_service.update_project(project_id, **update_data)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await audit_service.log(
        action="project.update",
        resource_type="project",
        user_id=current_user.id,
        resource_id=project.id,
        details=update_data,
        ip_address=request.client.host if request.client else None,
    )

    return APIResponse(
        message="Project updated successfully",
        data=ProjectResponse(
            id=project.id,
            name=project.name,
            client=project.client,
            description=project.description,
            status=project.status or "active",
            production_status=project.production_status or "not_started",
            owner_id=project.owner_id,
            owner_name=project.owner.full_name if project.owner else None,
            created_by_id=project.created_by_id,
            artwork_count=project.artwork_count,
            created_at=project.created_at,
            updated_at=project.updated_at,
        ),
    )


@router.delete("/{project_id}", response_model=APIResponse)
async def delete_project(
    project_id: str,
    request: Request,
    current_user: User = Depends(require_permission("Project.Delete")),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a project."""
    project_service = ProjectService(db)
    audit_service = AuditService(db)

    success = await project_service.soft_delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")

    await audit_service.log(
        action="project.delete",
        resource_type="project",
        user_id=current_user.id,
        resource_id=project_id,
        ip_address=request.client.host if request.client else None,
    )

    return APIResponse(message="Project deleted successfully")
