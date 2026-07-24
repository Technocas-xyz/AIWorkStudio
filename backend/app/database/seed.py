"""Database seed script - creates initial roles, permissions, and admin user."""

import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database.base import Base
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user import User
from app.services.auth_service import AuthService

settings = get_settings()


# Default roles
ROLES = [
    {"name": "super_admin", "display_name": "Super Administrator", "description": "Full system access"},
    {"name": "production_manager", "display_name": "Production Manager", "description": "Manages production workflows"},
    {"name": "designer", "display_name": "Designer", "description": "Creates and edits artwork"},
    {"name": "qa_officer", "display_name": "QA Officer", "description": "Reviews and approves artwork quality"},
    {"name": "operator", "display_name": "Operator", "description": "Operates production tasks"},
    {"name": "viewer", "display_name": "Viewer", "description": "Read-only access"},
]

# Default permissions
PERMISSIONS = [
    # Artwork permissions
    {"code": "Artwork.Create", "name": "Create Artwork", "module": "artwork"},
    {"code": "Artwork.Read", "name": "View Artwork", "module": "artwork"},
    {"code": "Artwork.Update", "name": "Edit Artwork", "module": "artwork"},
    {"code": "Artwork.Delete", "name": "Delete Artwork", "module": "artwork"},
    {"code": "Artwork.Generate", "name": "Generate Artwork", "module": "artwork"},
    {"code": "Artwork.Export", "name": "Export Artwork", "module": "artwork"},
    # Project permissions
    {"code": "Project.Create", "name": "Create Project", "module": "project"},
    {"code": "Project.Read", "name": "View Project", "module": "project"},
    {"code": "Project.Update", "name": "Edit Project", "module": "project"},
    {"code": "Project.Delete", "name": "Delete Project", "module": "project"},
    {"code": "Project.Archive", "name": "Archive Project", "module": "project"},
    # QA permissions
    {"code": "QA.Review", "name": "Review Quality", "module": "qa"},
    {"code": "QA.Approve", "name": "Approve Quality", "module": "qa"},
    {"code": "QA.Reject", "name": "Reject Quality", "module": "qa"},
    # Settings permissions
    {"code": "Settings.Manage", "name": "Manage Settings", "module": "settings"},
    {"code": "Settings.View", "name": "View Settings", "module": "settings"},
    # User management
    {"code": "Users.Create", "name": "Create Users", "module": "users"},
    {"code": "Users.Read", "name": "View Users", "module": "users"},
    {"code": "Users.Update", "name": "Edit Users", "module": "users"},
    {"code": "Users.Delete", "name": "Delete Users", "module": "users"},
    # Storage
    {"code": "Storage.Upload", "name": "Upload Files", "module": "storage"},
    {"code": "Storage.Download", "name": "Download Files", "module": "storage"},
    {"code": "Storage.Delete", "name": "Delete Files", "module": "storage"},
]

# Permission matrix - which roles get which permissions
ROLE_PERMISSIONS = {
    "super_admin": [p["code"] for p in PERMISSIONS],  # All permissions
    "production_manager": [
        "Artwork.Create", "Artwork.Read", "Artwork.Update", "Artwork.Generate", "Artwork.Export",
        "Project.Create", "Project.Read", "Project.Update", "Project.Archive",
        "QA.Review", "QA.Approve", "QA.Reject",
        "Settings.View",
        "Users.Read",
        "Storage.Upload", "Storage.Download",
    ],
    "designer": [
        "Artwork.Create", "Artwork.Read", "Artwork.Update", "Artwork.Generate",
        "Project.Read",
        "Storage.Upload", "Storage.Download",
    ],
    "qa_officer": [
        "Artwork.Read",
        "Project.Read",
        "QA.Review", "QA.Approve", "QA.Reject",
        "Storage.Download",
    ],
    "operator": [
        "Artwork.Read", "Artwork.Generate",
        "Project.Read",
        "Storage.Upload", "Storage.Download",
    ],
    "viewer": [
        "Artwork.Read",
        "Project.Read",
        "Settings.View",
        "Storage.Download",
    ],
}


def seed_database():
    """Seed the database with initial data."""
    engine = create_engine(settings.database_url_sync)

    with Session(engine) as session:
        # Create roles
        role_map = {}
        for role_data in ROLES:
            existing = session.query(Role).filter(Role.name == role_data["name"]).first()
            if existing:
                role_map[role_data["name"]] = existing
                continue

            role = Role(
                id=uuid.uuid4(),
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(role)
            role_map[role_data["name"]] = role

        session.flush()

        # Create permissions
        perm_map = {}
        for perm_data in PERMISSIONS:
            existing = session.query(Permission).filter(Permission.code == perm_data["code"]).first()
            if existing:
                perm_map[perm_data["code"]] = existing
                continue

            perm = Permission(
                id=uuid.uuid4(),
                code=perm_data["code"],
                name=perm_data["name"],
                module=perm_data["module"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(perm)
            perm_map[perm_data["code"]] = perm

        session.flush()

        # Assign permissions to roles
        for role_name, perm_codes in ROLE_PERMISSIONS.items():
            role = role_map[role_name]
            for code in perm_codes:
                perm = perm_map.get(code)
                if not perm:
                    continue

                existing = (
                    session.query(RolePermission)
                    .filter(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == perm.id,
                    )
                    .first()
                )
                if existing:
                    continue

                rp = RolePermission(
                    id=uuid.uuid4(),
                    role_id=role.id,
                    permission_id=perm.id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(rp)

        session.flush()

        # Create default admin user
        admin_role = role_map["super_admin"]
        existing_admin = session.query(User).filter(User.email == "admin@aiworkstudio.com").first()
        if not existing_admin:
            admin = User(
                id=uuid.uuid4(),
                email="admin@aiworkstudio.com",
                username="admin",
                hashed_password=AuthService.hash_password("Admin@123456"),
                first_name="System",
                last_name="Administrator",
                is_active=True,
                is_verified=True,
                role_id=admin_role.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(admin)

        session.commit()
        print("Database seeded successfully!")


if __name__ == "__main__":
    seed_database()
