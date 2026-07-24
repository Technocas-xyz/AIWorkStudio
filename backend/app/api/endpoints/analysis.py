"""Analysis endpoints - Artwork Intelligence Engine."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.schemas.common import APIResponse
from app.services.intelligence.orchestrator import AnalysisOrchestrator
from app.services.audit_service import AuditService
from app.api.deps import get_current_user
from app.models.user import User
from app.models.analysis import AnalysisJob, AnalysisReport

router = APIRouter()


@router.post("/start", response_model=APIResponse)
async def start_analysis(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start an analysis job for an artwork."""
    artwork_id = body.get("artwork_id")
    if not artwork_id:
        raise HTTPException(status_code=400, detail="artwork_id is required")

    engine = body.get("engine", "pillow")  # "pillow" or "gpt"
    if engine not in ("pillow", "gpt"):
        raise HTTPException(status_code=400, detail="engine must be 'pillow' or 'gpt'")

    orchestrator = AnalysisOrchestrator(db)
    audit_service = AuditService(db)

    try:
        job = await orchestrator.start_analysis(artwork_id, current_user.id, engine=engine)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Run analysis synchronously for now (in production, this would be a Celery task)
    report = await orchestrator.run_analysis(job.id, engine=engine)

    # Audit
    await audit_service.log(
        action="analysis.start",
        resource_type="analysis",
        user_id=current_user.id,
        resource_id=job.id,
        details={"artwork_id": artwork_id, "status": job.status, "engine": engine},
    )

    return APIResponse(
        message="Analysis completed" if job.status == "completed" else f"Analysis {job.status}",
        data={
            "job_id": job.id,
            "status": job.status,
            "progress": job.progress,
            "current_step": job.current_step,
            "version": job.version,
            "duration_seconds": job.duration_seconds,
            "engine": engine,
            "error": job.error_message,
        },
    )


@router.get("/{job_id}", response_model=APIResponse)
async def get_analysis_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get analysis job status."""
    orchestrator = AnalysisOrchestrator(db)
    job = await orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    return APIResponse(data={
        "job_id": job.id,
        "artwork_id": job.artwork_id,
        "status": job.status,
        "progress": job.progress,
        "current_step": job.current_step,
        "version": job.version,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "duration_seconds": job.duration_seconds,
        "error": job.error_message,
    })


@router.get("/{job_id}/status", response_model=APIResponse)
async def get_analysis_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get analysis job progress (for polling)."""
    orchestrator = AnalysisOrchestrator(db)
    job = await orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return APIResponse(data={
        "status": job.status,
        "progress": job.progress,
        "current_step": job.current_step,
    })


@router.get("/{job_id}/report", response_model=APIResponse)
async def get_analysis_report(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the full analysis report."""
    orchestrator = AnalysisOrchestrator(db)
    report = await orchestrator.get_report(job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return APIResponse(data={
        "id": report.id,
        "job_id": report.job_id,
        "artwork_id": report.artwork_id,
        "version": report.version,
        "overall_score": report.overall_score,
        "risk_level": report.risk_level,
        "file_inspection": json.loads(report.file_inspection) if report.file_inspection else None,
        "visual_analysis": json.loads(report.visual_analysis) if report.visual_analysis else None,
        "geometry_analysis": json.loads(report.geometry_analysis) if report.geometry_analysis else None,
        "production_analysis": json.loads(report.production_analysis) if report.production_analysis else None,
        "product_compatibility": json.loads(report.product_compatibility) if report.product_compatibility else None,
        "risk_assessment": json.loads(report.risk_assessment) if report.risk_assessment else None,
        "decision_plan": json.loads(report.decision_plan) if report.decision_plan else None,
        "generation_plan": json.loads(report.generation_plan) if report.generation_plan else None,
    })


@router.get("/{job_id}/plan", response_model=APIResponse)
async def get_generation_plan(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get just the Generation Plan JSON (for Module 4)."""
    orchestrator = AnalysisOrchestrator(db)
    report = await orchestrator.get_report(job_id)
    if not report or not report.generation_plan:
        raise HTTPException(status_code=404, detail="Generation plan not found")

    return APIResponse(data=json.loads(report.generation_plan))


@router.get("/artwork/{artwork_id}/latest", response_model=APIResponse)
async def get_latest_analysis(
    artwork_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest analysis report for an artwork."""
    orchestrator = AnalysisOrchestrator(db)
    report = await orchestrator.get_latest_report_for_artwork(artwork_id)
    if not report:
        return APIResponse(data=None, message="No analysis found for this artwork")

    return APIResponse(data={
        "id": report.id,
        "job_id": report.job_id,
        "artwork_id": report.artwork_id,
        "version": report.version,
        "overall_score": report.overall_score,
        "risk_level": report.risk_level,
        "generation_plan": json.loads(report.generation_plan) if report.generation_plan else None,
        "file_inspection": json.loads(report.file_inspection) if report.file_inspection else None,
        "visual_analysis": json.loads(report.visual_analysis) if report.visual_analysis else None,
        "geometry_analysis": json.loads(report.geometry_analysis) if report.geometry_analysis else None,
        "production_analysis": json.loads(report.production_analysis) if report.production_analysis else None,
        "product_compatibility": json.loads(report.product_compatibility) if report.product_compatibility else None,
        "risk_assessment": json.loads(report.risk_assessment) if report.risk_assessment else None,
        "decision_plan": json.loads(report.decision_plan) if report.decision_plan else None,
    })


@router.delete("/{job_id}", response_model=APIResponse)
async def delete_analysis(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete an analysis job."""
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.is_deleted = True
    await db.flush()
    return APIResponse(message="Analysis deleted")
