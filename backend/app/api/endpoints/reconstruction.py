"""Reconstruction Workspace API."""

import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.schemas.common import APIResponse
from app.api.deps import get_current_user
from app.models.user import User
from app.models.artwork import Artwork
from app.models.analysis import AnalysisReport
from app.models.reconstruction import ReconstructionPlan

router = APIRouter()


@router.post("/create", response_model=APIResponse)
async def create_reconstruction_plan(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a reconstruction plan from analysis report."""
    artwork_id = body.get("artwork_id")
    if not artwork_id:
        raise HTTPException(status_code=400, detail="artwork_id required")

    # Load artwork
    art_result = await db.execute(select(Artwork).where(Artwork.id == artwork_id, Artwork.is_deleted == False))
    artwork = art_result.scalar_one_or_none()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    # Load latest analysis
    report_result = await db.execute(
        select(AnalysisReport).where(AnalysisReport.artwork_id == artwork_id, AnalysisReport.is_deleted == False)
        .order_by(AnalysisReport.version.desc())
    )
    report = report_result.scalars().first()

    # Build strategy from analysis
    generation_plan = json.loads(report.generation_plan) if report and report.generation_plan else {}
    production_analysis = json.loads(report.production_analysis) if report and report.production_analysis else {}
    risk_assessment = json.loads(report.risk_assessment) if report and report.risk_assessment else {}

    # Auto-generate operations from analysis
    operations = _build_operations(generation_plan, production_analysis, risk_assessment, artwork)
    strategy = _build_strategy_summary(generation_plan, artwork)

    # Calculate estimates
    est_time = len([o for o in operations if o["enabled"]]) * 15  # ~15s per operation
    est_quality = min(100, (report.overall_score or 50) + len([o for o in operations if o["enabled"]]) * 3)

    plan = ReconstructionPlan(
        id=str(uuid.uuid4()),
        artwork_id=artwork_id,
        analysis_job_id=report.job_id if report else None,
        status="draft",
        strategy_summary=json.dumps(strategy),
        operations=json.dumps(operations),
        ai_model_primary=body.get("model", "gpt_image"),
        ai_model_fallback="flux",
        estimated_time_seconds=est_time,
        estimated_credits=len([o for o in operations if o["enabled"]]) * 0.5,
        estimated_quality_score=est_quality,
        estimated_similarity=95.0,
        target_width=artwork.width,
        target_height=artwork.height,
        target_dpi=300,
        created_by_id=current_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(plan)
    await db.flush()

    return APIResponse(message="Reconstruction plan created", data={
        "id": plan.id,
        "status": plan.status,
        "operations": operations,
        "strategy": strategy,
        "estimates": {
            "time_seconds": est_time,
            "credits": plan.estimated_credits,
            "quality_score": est_quality,
            "similarity": 95.0,
        },
    })


@router.get("/{plan_id}", response_model=APIResponse)
async def get_reconstruction_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ReconstructionPlan).where(ReconstructionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return APIResponse(data={
        "id": plan.id,
        "artwork_id": plan.artwork_id,
        "status": plan.status,
        "operations": json.loads(plan.operations) if plan.operations else [],
        "strategy": json.loads(plan.strategy_summary) if plan.strategy_summary else {},
        "ai_model_primary": plan.ai_model_primary,
        "ai_model_fallback": plan.ai_model_fallback,
        "target_dpi": plan.target_dpi,
        "estimates": {
            "time_seconds": plan.estimated_time_seconds,
            "credits": plan.estimated_credits,
            "quality_score": plan.estimated_quality_score,
            "similarity": plan.estimated_similarity,
        },
    })


@router.put("/{plan_id}", response_model=APIResponse)
async def update_reconstruction_plan(
    plan_id: str, body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ReconstructionPlan).where(ReconstructionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if "operations" in body:
        plan.operations = json.dumps(body["operations"])
    if "ai_model_primary" in body:
        plan.ai_model_primary = body["ai_model_primary"]
    if "target_dpi" in body:
        plan.target_dpi = body["target_dpi"]
    plan.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return APIResponse(message="Plan updated")


@router.post("/validate", response_model=APIResponse)
async def validate_plan(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Validate a reconstruction plan before approval."""
    plan_id = body.get("plan_id")
    result = await db.execute(select(ReconstructionPlan).where(ReconstructionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    operations = json.loads(plan.operations) if plan.operations else []
    enabled_ops = [o for o in operations if o.get("enabled")]

    errors = []
    warnings = []

    if not enabled_ops:
        errors.append("No operations selected")
    if not plan.ai_model_primary:
        errors.append("No AI model selected")

    # Check for conflicts
    has_bg_removal = any(o["id"] == "background_removal" for o in enabled_ops)
    has_bg_keep = any(o["id"] == "transparency_repair" for o in enabled_ops)
    if has_bg_removal and has_bg_keep:
        warnings.append("Both background removal and transparency repair selected - may conflict")

    valid = len(errors) == 0
    if valid:
        plan.status = "validated"
        await db.flush()

    return APIResponse(data={"valid": valid, "errors": errors, "warnings": warnings})


@router.post("/approve", response_model=APIResponse)
async def approve_plan(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan_id = body.get("plan_id")
    result = await db.execute(select(ReconstructionPlan).where(ReconstructionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan.status = "approved"
    plan.approved_by_id = current_user.id
    plan.approved_at = datetime.now(timezone.utc)
    await db.flush()
    return APIResponse(message="Plan approved - ready for AI Production")


def _build_operations(plan: dict, production: dict, risks: dict, artwork) -> list:
    """Build operation list from analysis results."""
    ops = []

    ops.append({"id": "canvas_expansion", "label": "Canvas Expansion", "enabled": plan.get("needs_canvas_expansion", False),
                "priority": 1, "description": "Expand canvas to add safe margins", "estimated_time": 10, "confidence": 0.85})
    ops.append({"id": "background_removal", "label": "Background Removal", "enabled": plan.get("needs_background_removal", False),
                "priority": 2, "description": "Remove background for transparent output", "estimated_time": 15, "confidence": 0.9})
    ops.append({"id": "super_resolution", "label": "AI Upscaling", "enabled": plan.get("needs_super_resolution", False),
                "priority": 3, "description": "Increase resolution to 300 DPI", "estimated_time": 20, "confidence": 0.85})
    ops.append({"id": "reconstruction", "label": "AI Reconstruction", "enabled": plan.get("needs_reconstruction", False),
                "priority": 4, "description": "Rebuild damaged or low-quality areas", "estimated_time": 30, "confidence": 0.75})
    ops.append({"id": "edge_refinement", "label": "Edge Refinement", "enabled": plan.get("needs_edge_refinement", False),
                "priority": 5, "description": "Smooth and clean all edges", "estimated_time": 10, "confidence": 0.8})
    ops.append({"id": "halo_removal", "label": "Halo Removal", "enabled": plan.get("needs_halo_removal", False),
                "priority": 6, "description": "Remove white/bright edge halos", "estimated_time": 10, "confidence": 0.8})
    ops.append({"id": "shadow_removal", "label": "Shadow Removal", "enabled": plan.get("needs_shadow_removal", False),
                "priority": 7, "description": "Remove drop shadows and cast shadows", "estimated_time": 10, "confidence": 0.75})
    ops.append({"id": "noise_reduction", "label": "Noise Reduction", "enabled": plan.get("needs_noise_reduction", False),
                "priority": 8, "description": "Remove grain, noise, and artifacts", "estimated_time": 10, "confidence": 0.85})
    ops.append({"id": "color_cleanup", "label": "Color Cleanup", "enabled": plan.get("needs_color_cleanup", False),
                "priority": 9, "description": "Normalize and clean colors for print", "estimated_time": 8, "confidence": 0.8})
    ops.append({"id": "vectorization", "label": "Vector Preparation", "enabled": plan.get("needs_vectorization", False),
                "priority": 10, "description": "Optimize for future vectorization", "estimated_time": 15, "confidence": 0.7})
    ops.append({"id": "transparency_repair", "label": "Transparency Repair", "enabled": False,
                "priority": 11, "description": "Fix damaged alpha channel", "estimated_time": 10, "confidence": 0.8})
    ops.append({"id": "text_preservation", "label": "Text Preservation", "enabled": plan.get("preserve_typography", False),
                "priority": 0, "description": "Protect all text elements during processing", "estimated_time": 0, "confidence": 0.95})

    return sorted(ops, key=lambda x: x["priority"])


def _build_strategy_summary(plan: dict, artwork) -> dict:
    return {
        "artwork_type": plan.get("artwork_type", "unknown"),
        "current_score": plan.get("overall_score", 0),
        "risk_level": plan.get("risk_level", "unknown"),
        "target_dpi": 300,
        "preserve_typography": plan.get("preserve_typography", True),
        "preserve_composition": plan.get("preserve_composition", True),
        "preserve_colors": plan.get("preserve_colors", True),
        "recommended_model": plan.get("recommended_model", "GPT Image"),
        "background_type": plan.get("background_type", "unknown"),
    }
