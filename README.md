# AI Work Studio

Enterprise-grade SaaS application for AI artwork production workflows.

## Architecture

```
├── backend/                 # Python FastAPI Backend
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   ├── database/       # Database configuration & seeds
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic layer
│   │   ├── workers/        # Celery background tasks
│   │   ├── config.py       # Application configuration
│   │   └── main.py         # FastAPI application entry
│   ├── alembic/            # Database migrations
│   ├── tests/              # Unit & integration tests
│   └── scripts/            # Utility scripts
├── frontend/               # Vue 3 Frontend
│   ├── src/
│   │   ├── assets/         # Styles and static assets
│   │   ├── components/     # Reusable Vue components
│   │   ├── composables/    # Vue composables
│   │   ├── layouts/        # Page layouts
│   │   ├── pages/          # Page components
│   │   ├── router/         # Vue Router configuration
│   │   ├── services/       # API service layer
│   │   ├── stores/         # Pinia stores
│   │   └── types/          # TypeScript type definitions
│   └── public/             # Static public assets
├── nginx/                  # Nginx reverse proxy config
├── docker-compose.yml      # Docker orchestration
└── .env                    # Environment configuration
```

## Technology Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Frontend    | Vue 3, TypeScript, Pinia, Tailwind CSS |
| Backend     | Python, FastAPI, SQLAlchemy, Alembic  |
| Database    | PostgreSQL 16                       |
| Cache       | Redis 7                             |
| Storage     | MinIO (S3-compatible)               |
| Workers     | Celery                              |
| Proxy       | Nginx                               |
| Container   | Docker, Docker Compose              |

## Quick Start

### Prerequisites

- Docker & Docker Compose installed
- Ports 3000, 8000, 8080, 5432, 6379, 9000, 9001 available

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-work-studio
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Start the application:
```bash
docker-compose up --build
```

4. Access the application:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/api/docs
- **Nginx Proxy**: http://localhost:8080
- **MinIO Console**: http://localhost:9001

### Default Credentials

| Service | User | Password |
|---------|------|----------|
| Application | admin@aiworkstudio.com | Admin@123456 |
| MinIO | minioadmin | minioadmin123 |
| PostgreSQL | aws_user | aws_dev_password_2024 |

## API Documentation

Available at http://localhost:8000/api/docs (Swagger UI) or http://localhost:8000/api/redoc (ReDoc).

### Authentication Flow

1. `POST /api/auth/login` — Returns access + refresh tokens
2. Include `Authorization: Bearer <token>` on all requests
3. `POST /api/auth/refresh` — Refresh expired access token
4. `POST /api/auth/logout` — Invalidate session

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/login | User login |
| POST | /api/auth/logout | User logout |
| POST | /api/auth/refresh | Refresh token |
| GET | /api/auth/me | Current user info |
| GET | /api/projects | List projects |
| POST | /api/projects | Create project |
| PUT | /api/projects/{id} | Update project |
| DELETE | /api/projects/{id} | Delete project |
| GET | /api/users | List users |
| POST | /api/users | Create user |
| PUT | /api/users/{id} | Update user |
| GET | /api/settings | Get settings |
| PUT | /api/settings | Update settings |
| GET | /api/dashboard/stats | Dashboard metrics |
| GET | /api/dashboard/recent-activity | Recent activity |

## User Roles

| Role | Description |
|------|-------------|
| Super Administrator | Full system access |
| Production Manager | Manages production workflows |
| Designer | Creates and edits artwork |
| QA Officer | Reviews and approves quality |
| Operator | Operates production tasks |
| Viewer | Read-only access |

## Permission Matrix

Permissions are dynamic and stored in the database. Each role has a configurable set of permissions. New permissions can be registered by future modules.

Core permissions: `Artwork.Create`, `Artwork.Read`, `Artwork.Update`, `Artwork.Delete`, `Artwork.Generate`, `Artwork.Export`, `Project.Create`, `Project.Read`, `Project.Update`, `Project.Delete`, `Project.Archive`, `QA.Review`, `QA.Approve`, `QA.Reject`, `Settings.Manage`, `Settings.View`, `Users.Create`, `Users.Read`, `Users.Update`, `Users.Delete`, `Storage.Upload`, `Storage.Download`, `Storage.Delete`

## Database Schema

### Tables
- **users** — User accounts
- **roles** — Role definitions
- **permissions** — Dynamic permission codes
- **role_permissions** — Role-permission assignments
- **projects** — Project management
- **project_members** — Project team members
- **storage_files** — File metadata
- **audit_logs** — Activity audit trail
- **system_settings** — Application configuration
- **notifications** — User notifications

All tables use UUID primary keys, timestamps (created_at, updated_at), and soft deletes (is_deleted).

## Storage Buckets (MinIO)

| Bucket | Purpose |
|--------|---------|
| original-artwork | Original artwork uploads |
| master-artwork | Master artwork files |
| variants | Artwork variants |
| reports | Generated reports |
| exports | Export files |
| temporary | Temporary files |

## Development

### Running Tests
```bash
cd backend
pip install pytest pytest-asyncio httpx aiosqlite
pytest tests/ -v
```

### Running Migrations
```bash
cd backend
alembic upgrade head
```

### Seeding Database
```bash
cd backend
python -m app.database.seed
```

## Workspaces

| Workspace | Status |
|-----------|--------|
| Dashboard | ✅ Active |
| Projects | ✅ Active |
| Artwork Library | 🚧 Module 2 |
| Analysis | 🚧 Module 2 |
| Reconstruction | 🚧 Module 2 |
| Production Planning | 🚧 Module 2 |
| Generation | 🚧 Module 2 |
| Quality | 🚧 Module 2 |
| Export | 🚧 Module 2 |
| Administration | 🚧 Module 2 |
| Settings | 🚧 Module 2 |

## License

Proprietary — All rights reserved.
