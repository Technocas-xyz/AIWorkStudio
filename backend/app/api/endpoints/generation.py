"""Generation endpoints - AI Production Studio."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.schemas.common import APIResponse
from app.services.production.orchestrator import ProductionOrchestrator
from app.services.production.model_registry import list_models
from app.services.audit_service import AuditService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


class GenerationStartRequest(BaseModel):
    artwork_id: str = Field(..., description="Artwork to generate from")
    model_name: str = Field(default="gpt_image", description="AI model to use")
    mode: str = Field(default="enhancement", description="Generation mode")
    operations: dict = Field(default_factory=dict, description="Selected operations")
    target_ratio: str = Field(default="", description="Target aspect ratio")
    custom_instructions: str = Field(default="", description="Additional instructions")


@router.post("/start", response_model=APIResponse)
async def start_generation(
    body: GenerationStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new generation job."""
    orchestrator = ProductionOrchestrator(db)
    audit_service = AuditService(db)

    valid_modes = ["reconstruction", "enhancement", "upscaling", "background_cleanup", "edge_refinement", "production_cleanup"]
    if body.mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Choose from: {valid_modes}")

    try:
        job = await orchestrator.start_generation(
            artwork_id=body.artwork_id,
            user_id=current_user.id,
            model_name=body.model_name,
            mode=body.mode,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Run generation with user settings
    candidate = await orchestrator.run_generation(
        job.id,
        operations=body.operations,
        custom_instructions=body.custom_instructions,
        target_ratio=body.target_ratio,
    )

    await audit_service.log(
        action="generation.start",
        resource_type="generation",
        user_id=current_user.id,
        resource_id=job.id,
        details={"model": body.model_name, "mode": body.mode, "status": job.status},
    )

    return APIResponse(
        message="Generation completed" if job.status == "completed" else f"Generation {job.status}",
        data={
            "job_id": job.id,
            "status": job.status,
            "progress": job.progress,
            "current_step": job.current_step,
            "model_name": job.model_name,
            "mode": job.mode,
            "duration_seconds": job.duration_seconds,
            "error": job.error_message,
            "candidate": _candidate_to_dict(candidate) if candidate else None,
        },
    )


@router.get("/{job_id}", response_model=APIResponse)
async def get_generation_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get generation job status."""
    orchestrator = ProductionOrchestrator(db)
    job = await orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return APIResponse(data={
        "job_id": job.id,
        "artwork_id": job.artwork_id,
        "status": job.status,
        "progress": job.progress,
        "current_step": job.current_step,
        "model_name": job.model_name,
        "mode": job.mode,
        "retry_count": job.retry_count,
        "duration_seconds": job.duration_seconds,
        "error": job.error_message,
    })


@router.get("/{job_id}/candidates", response_model=APIResponse)
async def get_candidates(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all candidates for a generation job."""
    orchestrator = ProductionOrchestrator(db)
    candidates = await orchestrator.get_candidates(job_id)
    return APIResponse(data=[_candidate_to_dict(c) for c in candidates])


@router.post("/{job_id}/approve", response_model=APIResponse)
async def approve_candidate(
    job_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a candidate as Master Artwork."""
    candidate_id = body.get("candidate_id")
    if not candidate_id:
        raise HTTPException(status_code=400, detail="candidate_id is required")

    orchestrator = ProductionOrchestrator(db)
    master = await orchestrator.approve_candidate(candidate_id, current_user.id)
    if not master:
        raise HTTPException(status_code=404, detail="Candidate not found")

    await AuditService(db).log(
        action="generation.approve",
        resource_type="master_artwork",
        user_id=current_user.id,
        resource_id=master.id,
        details={"candidate_id": candidate_id, "version": master.version},
    )

    return APIResponse(message="Master Artwork approved", data={
        "master_id": master.id,
        "version": master.version,
        "similarity_score": master.similarity_score,
        "quality_score": master.quality_score,
    })


@router.post("/{job_id}/reject", response_model=APIResponse)
async def reject_candidate(
    job_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject a candidate."""
    candidate_id = body.get("candidate_id")
    if not candidate_id:
        raise HTTPException(status_code=400, detail="candidate_id is required")

    orchestrator = ProductionOrchestrator(db)
    success = await orchestrator.reject_candidate(candidate_id)
    if not success:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return APIResponse(message="Candidate rejected")


@router.post("/{job_id}/retry", response_model=APIResponse)
async def retry_generation(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retry a failed or generate another candidate."""
    orchestrator = ProductionOrchestrator(db)
    candidate = await orchestrator.run_generation(job_id)

    job = await orchestrator.get_job(job_id)
    return APIResponse(
        message="Retry completed" if job and job.status == "completed" else "Retry failed",
        data={
            "status": job.status if job else "unknown",
            "candidate": _candidate_to_dict(candidate) if candidate else None,
            "error": job.error_message if job else None,
        },
    )


@router.post("/{job_id}/cancel", response_model=APIResponse)
async def cancel_generation(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a generation job."""
    from sqlalchemy import select
    from app.models.generation import GenerationJob
    result = await db.execute(select(GenerationJob).where(GenerationJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "cancelled"
    await db.flush()
    return APIResponse(message="Job cancelled")


@router.get("/artwork/{artwork_id}/history", response_model=APIResponse)
async def get_artwork_generation_history(
    artwork_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all generation jobs and candidates for an artwork."""
    from sqlalchemy import select
    from app.models.generation import GenerationJob, CandidateArtwork

    # Get latest completed job
    job_result = await db.execute(
        select(GenerationJob)
        .where(GenerationJob.artwork_id == artwork_id, GenerationJob.status == "completed", GenerationJob.is_deleted == False)
        .order_by(GenerationJob.created_at.desc())
    )
    latest_job = job_result.scalars().first()

    if not latest_job:
        return APIResponse(data={"job": None, "candidates": []})

    # Get all candidates for this artwork across all jobs
    cand_result = await db.execute(
        select(CandidateArtwork)
        .join(GenerationJob, GenerationJob.id == CandidateArtwork.job_id)
        .where(GenerationJob.artwork_id == artwork_id, CandidateArtwork.is_deleted == False)
        .order_by(CandidateArtwork.created_at.desc())
    )
    all_candidates = list(cand_result.scalars().all())

    return APIResponse(data={
        "job": {
            "job_id": latest_job.id,
            "status": latest_job.status,
            "model_name": latest_job.model_name,
            "mode": latest_job.mode,
            "duration_seconds": latest_job.duration_seconds,
        },
        "candidates": [_candidate_to_dict(c) for c in all_candidates],
    })


@router.get("/models/list", response_model=APIResponse)
async def get_available_models(
    current_user: User = Depends(get_current_user),
):
    """List all registered AI models."""
    models = list_models()
    return APIResponse(data=models)


def _candidate_to_dict(candidate) -> dict:
    if not candidate:
        return {}
    return {
        "id": candidate.id,
        "candidate_number": candidate.candidate_number,
        "model_name": candidate.model_name,
        "storage_path": candidate.storage_path,
        "file_size": candidate.file_size,
        "width": candidate.width,
        "height": candidate.height,
        "similarity_score": candidate.similarity_score,
        "quality_score": candidate.quality_score,
        "status": candidate.status,
        "post_processed": candidate.post_processed,
    }
