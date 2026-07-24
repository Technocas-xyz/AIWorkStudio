"""AI Work Studio - Main FastAPI Application."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.api.router import api_router
from app.database.session import engine

settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Auto-seed database on first run
    try:
        _auto_seed_database()
    except Exception as e:
        print(f"Auto-seed: {e}")

    # Only initialize MinIO in Docker mode
    if os.environ.get("APP_ENV") != "local":
        try:
            from app.services.storage_service import StorageService
            storage = StorageService()
            storage.initialize_buckets()
        except Exception as e:
            print(f"Warning: Could not initialize MinIO buckets: {e}")

    yield

    # Shutdown
    await engine.dispose()


def _auto_seed_database():
    """Create tables and seed default data if not already present."""
    import uuid
    from datetime import datetime, timezone
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.orm import Session
    from app.database.base import Base
    from app.config import get_settings

    settings = get_settings()

    # Build sync database URL
    if hasattr(settings, 'database_url_sync'):
        db_url = settings.database_url_sync
    elif 'sqlite' in getattr(settings, 'database_url', ''):
        db_url = settings.database_url.replace('+aiosqlite', '')
    else:
        # PostgreSQL async -> sync
        db_url = f"postgresql+psycopg2://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"

    sync_engine = create_engine(db_url, echo=False)

    # Import all models so metadata knows about them
    import app.models  # noqa - triggers all model imports

    # Create all tables
    Base.metadata.create_all(sync_engine)

    # Check if already seeded
    from app.models.role import Role
    with Session(sync_engine) as session:
        existing = session.query(Role).filter(Role.name == "super_admin").first()
        if existing:
            return  # Already seeded

    # Seed
    import bcrypt
    from app.models.user import User
    from app.models.role import Role
    from app.models.permission import Permission
    from app.models.role_permission import RolePermission

    now = datetime.now(timezone.utc)

    ROLES = [
        {"name": "super_admin", "display_name": "Super Administrator", "description": "Full system access"},
        {"name": "production_manager", "display_name": "Production Manager", "description": "Manages production workflows"},
        {"name": "designer", "display_name": "Designer", "description": "Creates and edits artwork"},
        {"name": "qa_officer", "display_name": "QA Officer", "description": "Reviews and approves quality"},
        {"name": "operator", "display_name": "Operator", "description": "Operates production tasks"},
        {"name": "viewer", "display_name": "Viewer", "description": "Read-only access"},
    ]

    PERMISSIONS = [
        {"code": "Artwork.Create", "name": "Create Artwork", "module": "artwork"},
        {"code": "Artwork.Read", "name": "View Artwork", "module": "artwork"},
        {"code": "Artwork.Update", "name": "Edit Artwork", "module": "artwork"},
        {"code": "Artwork.Delete", "name": "Delete Artwork", "module": "artwork"},
        {"code": "Artwork.Generate", "name": "Generate Artwork", "module": "artwork"},
        {"code": "Artwork.Export", "name": "Export Artwork", "module": "artwork"},
        {"code": "Project.Create", "name": "Create Project", "module": "project"},
        {"code": "Project.Read", "name": "View Project", "module": "project"},
        {"code": "Project.Update", "name": "Edit Project", "module": "project"},
        {"code": "Project.Delete", "name": "Delete Project", "module": "project"},
        {"code": "Project.Archive", "name": "Archive Project", "module": "project"},
        {"code": "QA.Review", "name": "Review Quality", "module": "qa"},
        {"code": "QA.Approve", "name": "Approve Quality", "module": "qa"},
        {"code": "QA.Reject", "name": "Reject Quality", "module": "qa"},
        {"code": "Settings.Manage", "name": "Manage Settings", "module": "settings"},
        {"code": "Settings.View", "name": "View Settings", "module": "settings"},
        {"code": "Users.Create", "name": "Create Users", "module": "users"},
        {"code": "Users.Read", "name": "View Users", "module": "users"},
        {"code": "Users.Update", "name": "Edit Users", "module": "users"},
        {"code": "Users.Delete", "name": "Delete Users", "module": "users"},
        {"code": "Storage.Upload", "name": "Upload Files", "module": "storage"},
        {"code": "Storage.Download", "name": "Download Files", "module": "storage"},
        {"code": "Storage.Delete", "name": "Delete Files", "module": "storage"},
    ]

    with Session(sync_engine) as session:
        role_map = {}
        for r in ROLES:
            role = Role(id=str(uuid.uuid4()), name=r["name"], display_name=r["display_name"], description=r["description"], created_at=now, updated_at=now)
            session.add(role)
            role_map[r["name"]] = role
        session.flush()

        perm_map = {}
        for p in PERMISSIONS:
            perm = Permission(id=str(uuid.uuid4()), code=p["code"], name=p["name"], module=p["module"], created_at=now, updated_at=now)
            session.add(perm)
            perm_map[p["code"]] = perm
        session.flush()

        # Give super_admin all permissions
        admin_role = role_map["super_admin"]
        for code, perm in perm_map.items():
            rp = RolePermission(id=str(uuid.uuid4()), role_id=admin_role.id, permission_id=perm.id, created_at=now, updated_at=now)
            session.add(rp)
        session.flush()

        # Create admin user
        admin = User(
            id=str(uuid.uuid4()),
            email="admin@aiworkstudio.com",
            username="admin",
            hashed_password=bcrypt.hashpw("Admin@123456".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            first_name="System",
            last_name="Administrator",
            is_active=True,
            is_verified=True,
            role_id=admin_role.id,
            created_at=now,
            updated_at=now,
        )
        session.add(admin)
        session.commit()
        print("✓ Database auto-seeded: admin@aiworkstudio.com / Admin@123456")


app = FastAPI(
    title=settings.app_name,
    description="Enterprise-grade SaaS application for AI artwork production workflows",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# State for rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

# Serve uploaded files in local dev mode
_uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
if os.path.isdir(_uploads_dir):
    app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An internal server error occurred.",
            "errors": [str(exc)] if settings.app_debug else [],
            "code": 500,
        },
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.app_name}
