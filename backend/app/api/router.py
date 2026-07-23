"""API router configuration."""

from fastapi import APIRouter

from app.api.endpoints import auth, projects, users, settings, dashboard, artworks, collections, tags, analysis, analysis_chat, generation, reconstruction, planning, qa

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(artworks.router, prefix="/artworks", tags=["Artworks"])
api_router.include_router(collections.router, prefix="/collections", tags=["Collections"])
api_router.include_router(tags.router, prefix="/tags", tags=["Tags"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(analysis_chat.router, prefix="/analysis", tags=["Analysis Chat"])
api_router.include_router(generation.router, prefix="/generation", tags=["Generation"])
api_router.include_router(reconstruction.router, prefix="/reconstruction", tags=["Reconstruction"])
api_router.include_router(planning.router, prefix="/planning", tags=["Production Planning"])
api_router.include_router(qa.router, prefix="/qa", tags=["Quality Assurance"])
