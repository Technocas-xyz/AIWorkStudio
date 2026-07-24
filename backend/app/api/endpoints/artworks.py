"""Artwork endpoints - upload, library, versions."""

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import APIResponse
from app.services.artwork_service import (
    ArtworkService, ArtworkValidationError, sanitize_filename,
    get_extension, ALL_SUPPORTED, RASTER_EXTENSIONS
)
from app.services.preview_service import generate_previews
from app.services.audit_service import AuditService
from app.api.deps import get_current_user, require_permission
from app.models.user import User
from app.models.artwork import Artwork
from app.models.artwork_preview import ArtworkPreview

router = APIRouter()

# Local file storage path for development (no MinIO)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "originals"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "previews"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "versions"), exist_ok=True)


def save_file_locally(bucket: str, path: str, data: bytes) -> str:
    """Save file to local filesystem (dev mode)."""
    full_dir = os.path.join(UPLOAD_DIR, bucket, os.path.dirname(path))
    os.makedirs(full_dir, exist_ok=True)
    full_path = os.path.join(UPLOAD_DIR, bucket, path)
    with open(full_path, "wb") as f:
        f.write(data)
    return full_path


@router.post("/upload", response_model=APIResponse)
async def upload_artwork(
    request: Request,
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    current_user: User = Depends(require_permission("Artwork.Create")),
    db: AsyncSession = Depends(get_db),
):
    """Upload a single artwork file."""
    artwork_service = ArtworkService(db)
    audit_service = AuditService(db)

    # Read file
    content = await file.read()
    file_size = len(content)
    original_filename = sanitize_filename(file.filename or "unnamed")

    # Validate
    try:
        metadata = artwork_service.validate_upload(original_filename, file_size, content)
    except ArtworkValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Generate checksum
    checksum = hashlib.sha256(content).hexdigest()

    # Check duplicate
    existing = await artwork_service.check_duplicate(checksum)
    if existing:
        return APIResponse(
            success=False,
            message="Duplicate file detected.",
            code=409,
            data={
                "duplicate": True,
                "existing_id": existing.id,
                "existing_artwork_id": existing.artwork_id,
                "existing_filename": existing.original_filename,
            },
        )

    # Store file
    ext = get_extension(original_filename)
    stored_filename = f"{uuid.uuid4()}.{ext}"
    storage_path = f"{datetime.utcnow().strftime('%Y/%m/%d')}/{stored_filename}"
    save_file_locally("originals", storage_path, content)

    # Create artwork record
    artwork = await artwork_service.create_artwork(
        filename=stored_filename,
        original_filename=original_filename,
        file_size=file_size,
        checksum=checksum,
        storage_bucket="originals",
        storage_path=storage_path,
        metadata=metadata,
        project_id=project_id,
        owner_id=current_user.id,
    )

    # Generate previews for raster images
    if ext in RASTER_EXTENSIONS and ext not in {"psd", "psb"}:
        previews = generate_previews(content, artwork.id)
        for preview_type, preview_data in previews.items():
            preview_path = f"{artwork.id}/{preview_type}.png"
            save_file_locally("previews", preview_path, preview_data["bytes"])

            preview_record = ArtworkPreview(
                id=str(uuid.uuid4()),
                artwork_id=artwork.id,
                preview_type=preview_type,
                width=preview_data["width"],
                height=preview_data["height"],
                storage_path=f"previews/{preview_path}",
                file_size=len(preview_data["bytes"]),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(preview_record)
        await db.flush()

    # Audit
    await audit_service.log(
        action="artwork.upload",
        resource_type="artwork",
        user_id=current_user.id,
        resource_id=artwork.id,
        details={"filename": original_filename, "size": file_size},
        ip_address=request.client.host if request.client else None,
    )

    return APIResponse(
        message="Artwork uploaded successfully",
        data=_artwork_to_dict(artwork),
    )


@router.post("/bulk-upload", response_model=APIResponse)
async def bulk_upload_artworks(
    request: Request,
    files: list[UploadFile] = File(...),
    project_id: Optional[str] = Form(None),
    current_user: User = Depends(require_permission("Artwork.Create")),
    db: AsyncSession = Depends(get_db),
):
    """Upload multiple artwork files."""
    artwork_service = ArtworkService(db)
    results = {"success": [], "failed": []}

    for file in files:
        content = await file.read()
        file_size = len(content)
        original_filename = sanitize_filename(file.filename or "unnamed")

        try:
            metadata = artwork_service.validate_upload(original_filename, file_size, content)
            checksum = hashlib.sha256(content).hexdigest()

            existing = await artwork_service.check_duplicate(checksum)
            if existing:
                results["failed"].append({"filename": original_filename, "error": "Duplicate file"})
                continue

            ext = get_extension(original_filename)
            stored_filename = f"{uuid.uuid4()}.{ext}"
            storage_path = f"{datetime.utcnow().strftime('%Y/%m/%d')}/{stored_filename}"
            save_file_locally("originals", storage_path, content)

            artwork = await artwork_service.create_artwork(
                filename=stored_filename,
                original_filename=original_filename,
                file_size=file_size,
                checksum=checksum,
                storage_bucket="originals",
                storage_path=storage_path,
                metadata=metadata,
                project_id=project_id,
                owner_id=current_user.id,
            )

            # Generate previews
            if ext in RASTER_EXTENSIONS and ext not in {"psd", "psb"}:
                previews = generate_previews(content, artwork.id)
                for preview_type, preview_data in previews.items():
                    preview_path = f"{artwork.id}/{preview_type}.png"
                    save_file_locally("previews", preview_path, preview_data["bytes"])
                    preview_record = ArtworkPreview(
                        id=str(uuid.uuid4()),
                        artwork_id=artwork.id,
                        preview_type=preview_type,
                        width=preview_data["width"],
                        height=preview_data["height"],
                        storage_path=f"previews/{preview_path}",
                        file_size=len(preview_data["bytes"]),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.add(preview_record)

            results["success"].append({"filename": original_filename, "id": artwork.id, "artwork_id": artwork.artwork_id})

        except ArtworkValidationError as e:
            results["failed"].append({"filename": original_filename, "error": str(e)})
        except Exception as e:
            results["failed"].append({"filename": original_filename, "error": f"Upload failed: {str(e)}"})

    await db.flush()

    return APIResponse(
        message=f"Uploaded {len(results['success'])} file(s), {len(results['failed'])} failed.",
        data=results,
    )


@router.get("", response_model=APIResponse)
async def list_artworks(
    page: int = Query(1, ge=1),
    page_size: int = Query(40, ge=1, le=200),
    search: Optional[str] = Query(None),
    extension: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List artworks with pagination and filters."""
    artwork_service = ArtworkService(db)
    result = await artwork_service.list_artworks(
        page=page, page_size=page_size, search=search,
        extension=extension, project_id=project_id, status=status,
        sort_by=sort_by, sort_order=sort_order,
    )
    return APIResponse(data={
        "items": [_artwork_to_dict(a) for a in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"],
    })


@router.get("/{artwork_id}", response_model=APIResponse)
async def get_artwork(
    artwork_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get artwork details."""
    artwork_service = ArtworkService(db)
    artwork = await artwork_service.get_artwork_by_id(artwork_id)
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    return APIResponse(data=_artwork_to_dict(artwork))


@router.put("/{artwork_id}", response_model=APIResponse)
async def update_artwork(
    artwork_id: str,
    body: dict,
    current_user: User = Depends(require_permission("Artwork.Update")),
    db: AsyncSession = Depends(get_db),
):
    """Update artwork metadata."""
    artwork_service = ArtworkService(db)
    allowed_fields = {"project_id", "status", "is_favorite"}
    update_data = {k: v for k, v in body.items() if k in allowed_fields}
    artwork = await artwork_service.update_artwork(artwork_id, **update_data)
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    return APIResponse(data=_artwork_to_dict(artwork), message="Artwork updated")


@router.delete("/{artwork_id}", response_model=APIResponse)
async def delete_artwork(
    artwork_id: str,
    current_user: User = Depends(require_permission("Artwork.Delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete an artwork."""
    artwork_service = ArtworkService(db)
    success = await artwork_service.soft_delete_artwork(artwork_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Artwork not found")
    return APIResponse(message="Artwork deleted")


@router.get("/{artwork_id}/versions", response_model=APIResponse)
async def get_artwork_versions(
    artwork_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get version history."""
    artwork_service = ArtworkService(db)
    versions = await artwork_service.get_versions(artwork_id)
    return APIResponse(data=[
        {
            "id": v.id,
            "version_number": v.version_number,
            "version_type": v.version_type,
            "filename": v.filename,
            "file_size": v.file_size,
            "width": v.width,
            "height": v.height,
            "notes": v.notes,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ])


@router.post("/{artwork_id}/versions", response_model=APIResponse)
async def create_artwork_version(
    artwork_id: str,
    file: UploadFile = File(...),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(require_permission("Artwork.Update")),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new version."""
    artwork_service = ArtworkService(db)
    content = await file.read()
    file_size = len(content)
    original_filename = sanitize_filename(file.filename or "unnamed")
    checksum = hashlib.sha256(content).hexdigest()

    ext = get_extension(original_filename)
    stored_filename = f"{uuid.uuid4()}.{ext}"
    storage_path = f"versions/{artwork_id}/{stored_filename}"
    save_file_locally("versions", f"{artwork_id}/{stored_filename}", content)

    # Get dimensions
    width, height = None, None
    if ext in RASTER_EXTENSIONS and ext not in {"psd", "psb"}:
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(content))
            width, height = img.width, img.height
            img.close()
        except Exception:
            pass

    version = await artwork_service.create_version(
        artwork_id=artwork_id,
        filename=stored_filename,
        file_size=file_size,
        checksum=checksum,
        storage_bucket="versions",
        storage_path=storage_path,
        width=width, height=height,
        user_id=current_user.id,
        notes=notes,
    )
    if not version:
        raise HTTPException(status_code=404, detail="Artwork not found")

    return APIResponse(message="Version created", data={
        "id": version.id,
        "version_number": version.version_number,
    })


@router.post("/{artwork_id}/favorite", response_model=APIResponse)
async def toggle_favorite(
    artwork_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle artwork favorite status."""
    artwork_service = ArtworkService(db)
    result = await artwork_service.toggle_favorite(artwork_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Artwork not found")
    return APIResponse(data={"is_favorite": result})


def _artwork_to_dict(artwork: Artwork) -> dict:
    """Convert artwork model to response dict."""
    return {
        "id": artwork.id,
        "artwork_id": artwork.artwork_id,
        "filename": artwork.filename,
        "original_filename": artwork.original_filename,
        "extension": artwork.extension,
        "mime_type": artwork.mime_type,
        "width": artwork.width,
        "height": artwork.height,
        "resolution_dpi": artwork.resolution_dpi,
        "color_space": artwork.color_space,
        "bit_depth": artwork.bit_depth,
        "has_transparency": artwork.has_transparency,
        "has_alpha_channel": artwork.has_alpha_channel,
        "orientation": artwork.orientation,
        "file_size": artwork.file_size,
        "checksum": artwork.checksum,
        "storage_bucket": artwork.storage_bucket,
        "storage_path": artwork.storage_path,
        "status": artwork.status,
        "processing_status": artwork.processing_status,
        "current_version": artwork.current_version,
        "project_id": artwork.project_id,
        "owner_id": artwork.owner_id,
        "is_favorite": artwork.is_favorite,
        "created_at": artwork.created_at.isoformat() if artwork.created_at else None,
        "updated_at": artwork.updated_at.isoformat() if artwork.updated_at else None,
    }
