"""Local development runner - uses SQLite, no Docker required."""

import os
import sys
import uuid
from datetime import datetime, timezone

# Ensure we're in the backend directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment before imports
os.environ["APP_ENV"] = "local"


def init_database():
    """Create tables and seed data using SQLite."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.database.base import Base
    from app.models import (
        User, Role, Permission, RolePermission,
        Project, ProjectMember, StorageFile, AuditLog,
        SystemSetting, Notification,
    )
    import bcrypt

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dev.db")
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    # Create all tables
    Base.metadata.create_all(engine)
    print("Database tables created.")

    now = datetime.utcnow()

    with Session(engine) as session:
        # Check if already seeded
        existing_role = session.query(Role).filter(Role.name == "super_admin").first()
        if existing_role:
            print("Database already seeded.")
            return

        # Roles
        roles_data = [
            {"name": "super_admin", "display_name": "Super Administrator", "description": "Full system access"},
            {"name": "production_manager", "display_name": "Production Manager", "description": "Manages production workflows"},
            {"name": "designer", "display_name": "Designer", "description": "Creates and edits artwork"},
            {"name": "qa_officer", "display_name": "QA Officer", "description": "Reviews and approves quality"},
            {"name": "operator", "display_name": "Operator", "description": "Operates production tasks"},
            {"name": "viewer", "display_name": "Viewer", "description": "Read-only access"},
        ]

        role_map = {}
        for r in roles_data:
            role = Role(
                id=str(uuid.uuid4()), name=r["name"], display_name=r["display_name"],
                description=r["description"], created_at=now, updated_at=now,
            )
            session.add(role)
            role_map[r["name"]] = role

        session.flush()

        # Permissions
        permissions_data = [
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

        perm_map = {}
        for p in permissions_data:
            perm = Permission(
                id=str(uuid.uuid4()), code=p["code"], name=p["name"], module=p["module"],
                created_at=now, updated_at=now,
            )
            session.add(perm)
            perm_map[p["code"]] = perm

        session.flush()

        # Give super_admin all permissions
        admin_role = role_map["super_admin"]
        for code, perm in perm_map.items():
            rp = RolePermission(
                id=str(uuid.uuid4()), role_id=admin_role.id, permission_id=perm.id,
                created_at=now, updated_at=now,
            )
            session.add(rp)

        # Give production_manager relevant permissions
        pm_perms = [
            "Artwork.Create", "Artwork.Read", "Artwork.Update", "Artwork.Generate", "Artwork.Export",
            "Project.Create", "Project.Read", "Project.Update", "Project.Delete", "Project.Archive",
            "QA.Review", "QA.Approve", "QA.Reject", "Settings.View", "Users.Read",
            "Storage.Upload", "Storage.Download",
        ]
        pm_role = role_map["production_manager"]
        for code in pm_perms:
            rp = RolePermission(
                id=str(uuid.uuid4()), role_id=pm_role.id, permission_id=perm_map[code].id,
                created_at=now, updated_at=now,
            )
            session.add(rp)

        # Give designer permissions
        designer_perms = ["Artwork.Create", "Artwork.Read", "Artwork.Update", "Artwork.Generate", "Project.Read", "Storage.Upload", "Storage.Download"]
        designer_role = role_map["designer"]
        for code in designer_perms:
            rp = RolePermission(id=str(uuid.uuid4()), role_id=designer_role.id, permission_id=perm_map[code].id, created_at=now, updated_at=now)
            session.add(rp)

        # Give viewer permissions
        viewer_perms = ["Artwork.Read", "Project.Read", "Settings.View", "Storage.Download"]
        viewer_role = role_map["viewer"]
        for code in viewer_perms:
            rp = RolePermission(id=str(uuid.uuid4()), role_id=viewer_role.id, permission_id=perm_map[code].id, created_at=now, updated_at=now)
            session.add(rp)

        session.flush()

        # Admin user
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
        print("Database seeded successfully!")
        print("  Login: admin@aiworkstudio.com / Admin@123456")


if __name__ == "__main__":
    init_database()

    # Start uvicorn
    import uvicorn
    print("\nStarting AI Work Studio API on http://localhost:8000")
    print("API Docs: http://localhost:8000/api/docs\n")
    uvicorn.run("app.main_local:app", host="0.0.0.0", port=8000, reload=False)
