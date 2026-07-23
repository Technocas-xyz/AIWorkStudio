"""Artwork service - handles upload, validation, metadata extraction, and DAM operations."""

import hashlib
import io
import json
import math
import os
import random
import string
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.models.artwork import Artwork
from app.models.artwork_version import ArtworkVersion
from app.models.artwork_metadata import ArtworkMetadata
from app.models.artwork_activity import ArtworkActivity
from app.models.artwork_preview import ArtworkPreview
from app.models.artwork_tag import ArtworkTag
from app.models.tag import Tag

# Supported formats
RASTER_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "tiff", "tif", "bmp", "psd", "psb"}
VECTOR_EXTENSIONS = {"svg", "ai", "eps", "pdf"}
ALL_SUPPORTED = RASTER_EXTENSIONS | VECTOR_EXTENSIONS

MIME_MAP = {
    "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "webp": "image/webp", "tiff": "image/tiff", "tif": "image/tiff",
    "bmp": "image/bmp", "psd": "image/vnd.adobe.photoshop",
    "psb": "image/vnd.adobe.photoshop", "svg": "image/svg+xml",
    "ai": "application/postscript", "eps": "application/postscript",
    "pdf": "application/pdf",
}

MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
MIN_DIMENSION = 10
MAX_DIMENSION = 50000

# Dangerous extensions to block
BLOCKED_EXTENSIONS = {"exe", "bat", "cmd", "sh", "ps1", "vbs", "js", "msi", "dll", "com", "scr"}


def generate_artwork_id() -> str:
    """Generate a unique human-readable artwork ID like AWS-A7K3M2."""
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=6))
    return f"AWS-{suffix}"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and injection."""
    # Remove path separators
    name = os.path.basename(filename)
    # Remove any null bytes or control characters
    name = ''.join(c for c in name if c.isprintable() and c not in '<>:"/\\|?*')
    # Limit length
    if len(name) > 200:
        ext = name.rsplit('.', 1)[-1] if '.' in name else ''
        name = name[:195] + '.' + ext if ext else name[:200]
    return name or "unnamed_file"


def get_extension(filename: str) -> str:
    """Extract and normalize file extension."""
    if '.' in filename:
        return filename.rsplit('.', 1)[-1].lower()
    return ""


class ArtworkValidationError(Exception):
    """Raised when artwork validation fails."""
    pass


class ArtworkService:
    """Core artwork/DAM business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def validate_upload(self, filename: str, file_size: int, content_bytes: bytes) -> dict:
        """Validate an uploaded file. Returns metadata dict or raises ArtworkValidationError."""
        ext = get_extension(filename)

        # Check blocked extensions
        if ext in BLOCKED_EXTENSIONS:
            raise ArtworkValidationError(f"File type '.{ext}' is not allowed for security reasons.")

        # Check supported extension
        if ext not in ALL_SUPPORTED:
            raise ArtworkValidationError(
                f"Unsupported file type '.{ext}'. Supported: {', '.join(sorted(ALL_SUPPORTED))}"
            )

        # Check empty file
        if file_size == 0 or len(content_bytes) == 0:
            raise ArtworkValidationError("File is empty.")

        # Check max size
        if file_size > MAX_FILE_SIZE:
            raise ArtworkValidationError(
                f"File exceeds maximum size of {MAX_FILE_SIZE // (1024*1024)} MB."
            )

        # Extract image metadata for raster files
        metadata = {
            "width": None, "height": None, "resolution_dpi": None,
            "color_space": None, "bit_depth": None,
            "has_transparency": False, "has_alpha_channel": False,
            "orientation": None,
        }

        if ext in RASTER_EXTENSIONS and ext not in {"psd", "psb"}:
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(content_bytes))
                metadata["width"] = img.width
                metadata["height"] = img.height
                metadata["color_space"] = img.mode
                metadata["has_alpha_channel"] = img.mode in ("RGBA", "LA", "PA")
                metadata["has_transparency"] = metadata["has_alpha_channel"]

                # DPI
                dpi = img.info.get("dpi")
                if dpi:
                    metadata["resolution_dpi"] = int(dpi[0]) if isinstance(dpi, tuple) else int(dpi)

                # Bit depth
                if img.mode == "1":
                    metadata["bit_depth"] = 1
                elif img.mode in ("L", "P"):
                    metadata["bit_depth"] = 8
                elif img.mode in ("RGB", "YCbCr"):
                    metadata["bit_depth"] = 24
                elif img.mode == "RGBA":
                    metadata["bit_depth"] = 32
                elif img.mode == "I":
                    metadata["bit_depth"] = 32
                elif img.mode == "F":
                    metadata["bit_depth"] = 32

                # Orientation
                if img.width > img.height:
                    metadata["orientation"] = "landscape"
                elif img.height > img.width:
                    metadata["orientation"] = "portrait"
                else:
                    metadata["orientation"] = "square"

                # Validate dimensions
                if img.width < MIN_DIMENSION or img.height < MIN_DIMENSION:
                    raise ArtworkValidationError(
                        f"Image dimensions too small ({img.width}x{img.height}). Minimum is {MIN_DIMENSION}px."
                    )
                if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
                    raise ArtworkValidationError(
                        f"Image dimensions too large ({img.width}x{img.height}). Maximum is {MAX_DIMENSION}px."
                    )

                img.close()
            except ArtworkValidationError:
                raise
            except Exception as e:
                raise ArtworkValidationError(f"File appears to be corrupt or unreadable: {str(e)}")

        return metadata

    async def check_duplicate(self, checksum: str) -> Optional[Artwork]:
        """Check if artwork with same checksum already exists."""
        result = await self.db.execute(
            select(Artwork).where(Artwork.checksum == checksum, Artwork.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def create_artwork(
        self,
        filename: str,
        original_filename: str,
        file_size: int,
        checksum: str,
        storage_bucket: str,
        storage_path: str,
        metadata: dict,
        project_id: Optional[str],
        owner_id: str,
    ) -> Artwork:
        """Create a new artwork record."""
        ext = get_extension(original_filename)
        mime_type = MIME_MAP.get(ext, "application/octet-stream")

        artwork = Artwork(
            id=str(uuid.uuid4()),
            artwork_id=generate_artwork_id(),
            filename=filename,
            original_filename=original_filename,
            extension=ext,
            mime_type=mime_type,
            width=metadata.get("width"),
            height=metadata.get("height"),
            resolution_dpi=metadata.get("resolution_dpi"),
            color_space=metadata.get("color_space"),
            bit_depth=metadata.get("bit_depth"),
            has_transparency=metadata.get("has_transparency", False),
            has_alpha_channel=metadata.get("has_alpha_channel", False),
            orientation=metadata.get("orientation"),
            file_size=file_size,
            checksum=checksum,
            storage_bucket=storage_bucket,
            storage_path=storage_path,
            status="active",
            processing_status="completed",
            current_version=1,
            project_id=project_id,
            owner_id=owner_id,
            uploaded_by_id=owner_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(artwork)
        await self.db.flush()

        # Create initial version
        version = ArtworkVersion(
            id=str(uuid.uuid4()),
            artwork_id=artwork.id,
            version_number=1,
            version_type="upload",
            filename=filename,
            file_size=file_size,
            checksum=checksum,
            storage_bucket=storage_bucket,
            storage_path=storage_path,
            width=metadata.get("width"),
            height=metadata.get("height"),
            created_by_id=owner_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(version)

        # Log activity
        activity = ArtworkActivity(
            id=str(uuid.uuid4()),
            artwork_id=artwork.id,
            user_id=owner_id,
            action="upload",
            details=json.dumps({"filename": original_filename, "size": file_size}),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(activity)

        await self.db.flush()
        await self.db.refresh(artwork)
        return artwork

    async def get_artwork_by_id(self, artwork_id: str) -> Optional[Artwork]:
        """Get artwork by UUID or artwork_id code."""
        result = await self.db.execute(
            select(Artwork).where(
                or_(Artwork.id == artwork_id, Artwork.artwork_id == artwork_id),
                Artwork.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def list_artworks(
        self,
        page: int = 1,
        page_size: int = 40,
        search: Optional[str] = None,
        extension: Optional[str] = None,
        project_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> dict:
        """List artworks with pagination and filters."""
        query = select(Artwork).where(Artwork.is_deleted == False)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Artwork.original_filename.ilike(search_filter),
                    Artwork.artwork_id.ilike(search_filter),
                )
            )

        if extension:
            query = query.where(Artwork.extension == extension.lower())

        if project_id:
            query = query.where(Artwork.project_id == project_id)

        if owner_id:
            query = query.where(Artwork.owner_id == owner_id)

        if status:
            query = query.where(Artwork.status == status)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Sort
        sort_col = getattr(Artwork, sort_by, Artwork.created_at)
        if sort_order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        artworks = result.scalars().all()

        return {
            "items": artworks,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        }

    async def update_artwork(self, artwork_id: str, **kwargs) -> Optional[Artwork]:
        """Update artwork fields."""
        artwork = await self.get_artwork_by_id(artwork_id)
        if not artwork:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(artwork, key):
                setattr(artwork, key, value)
        artwork.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(artwork)
        return artwork

    async def soft_delete_artwork(self, artwork_id: str, user_id: str) -> bool:
        """Soft delete an artwork."""
        artwork = await self.get_artwork_by_id(artwork_id)
        if not artwork:
            return False
        artwork.is_deleted = True
        artwork.status = "deleted"

        activity = ArtworkActivity(
            id=str(uuid.uuid4()),
            artwork_id=artwork.id,
            user_id=user_id,
            action="delete",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(activity)
        await self.db.flush()
        return True

    async def get_versions(self, artwork_id: str) -> list:
        """Get all versions of an artwork."""
        artwork = await self.get_artwork_by_id(artwork_id)
        if not artwork:
            return []
        result = await self.db.execute(
            select(ArtworkVersion)
            .where(ArtworkVersion.artwork_id == artwork.id, ArtworkVersion.is_deleted == False)
            .order_by(ArtworkVersion.version_number.desc())
        )
        return list(result.scalars().all())

    async def create_version(
        self, artwork_id: str, filename: str, file_size: int,
        checksum: str, storage_bucket: str, storage_path: str,
        width: Optional[int], height: Optional[int],
        user_id: str, notes: Optional[str] = None,
    ) -> Optional[ArtworkVersion]:
        """Create a new version for an artwork."""
        artwork = await self.get_artwork_by_id(artwork_id)
        if not artwork:
            return None

        new_version_num = artwork.current_version + 1
        version = ArtworkVersion(
            id=str(uuid.uuid4()),
            artwork_id=artwork.id,
            version_number=new_version_num,
            version_type="edit",
            filename=filename,
            file_size=file_size,
            checksum=checksum,
            storage_bucket=storage_bucket,
            storage_path=storage_path,
            width=width,
            height=height,
            notes=notes,
            created_by_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(version)
        artwork.current_version = new_version_num
        artwork.updated_at = datetime.now(timezone.utc)

        activity = ArtworkActivity(
            id=str(uuid.uuid4()),
            artwork_id=artwork.id,
            user_id=user_id,
            action="version_create",
            details=json.dumps({"version": new_version_num}),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(activity)
        await self.db.flush()
        return version

    async def toggle_favorite(self, artwork_id: str) -> Optional[bool]:
        """Toggle favorite status."""
        artwork = await self.get_artwork_by_id(artwork_id)
        if not artwork:
            return None
        artwork.is_favorite = not artwork.is_favorite
        await self.db.flush()
        return artwork.is_favorite

    async def get_stats(self) -> dict:
        """Get artwork statistics."""
        total = await self.db.execute(
            select(func.count(Artwork.id)).where(Artwork.is_deleted == False)
        )
        total_size = await self.db.execute(
            select(func.coalesce(func.sum(Artwork.file_size), 0)).where(Artwork.is_deleted == False)
        )
        return {
            "total_artworks": total.scalar() or 0,
            "total_storage_bytes": total_size.scalar() or 0,
        }
