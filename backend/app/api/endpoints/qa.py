"""Quality Assurance endpoints."""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.schemas.common import APIResponse
from app.services.qa_engine import QAEngine
from app.services.audit_service import AuditService
from app.api.deps import get_current_user
from app.models.user import User
from app.models.qa import QAReport

router = APIRouter()


@router.post("/start", response_model=APIResponse)
async def start_qa(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start QA inspection for an artwork."""
    artwork_id = body.get("artwork_id")
    if not artwork_id:
        raise HTTPException(status_code=400, detail="artwork_id required")

    engine = QAEngine(db)
    try:
        report = await engine.start_inspection(artwork_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Run inspection
    report = await engine.run_inspection(report.id)

    await AuditService(db).log(action="qa.start", resource_type="qa", user_id=current_user.id, resource_id=report.id)

    return APIResponse(message="QA inspection completed", data=_report_to_dict(report))


@router.get("/{report_id}", response_model=APIResponse)
async def get_qa_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QAReport).where(QAReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return APIResponse(data=_report_to_dict(report))


@router.get("/{report_id}/report", response_model=APIResponse)
async def get_full_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QAReport).where(QAReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return APIResponse(data=_report_to_dict(report))


@router.post("/{report_id}/approve", response_model=APIResponse)
async def approve_qa(
    report_id: str, body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = QAEngine(db)
    success = await engine.approve(report_id, current_user.id, body.get("notes", ""))
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    await AuditService(db).log(action="qa.approve", resource_type="qa", user_id=current_user.id, resource_id=report_id)
    return APIResponse(message="QA Approved — artwork cleared for production")


@router.post("/{report_id}/reject", response_model=APIResponse)
async def reject_qa(
    report_id: str, body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = QAEngine(db)
    success = await engine.reject(report_id, current_user.id, body.get("notes", ""))
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    await AuditService(db).log(action="qa.reject", resource_type="qa", user_id=current_user.id, resource_id=report_id)
    return APIResponse(message="QA Rejected")


@router.post("/{report_id}/send-back", response_model=APIResponse)
async def send_back(
    report_id: str, body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target = body.get("target", "reconstruction")  # reconstruction or ai_production
    notes = body.get("notes", "")
    engine = QAEngine(db)
    success = await engine.send_back(report_id, current_user.id, target, notes)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    await AuditService(db).log(action="qa.send_back", resource_type="qa", user_id=current_user.id, resource_id=report_id, details={"target": target})
    return APIResponse(message=f"Sent back to {target.replace('_', ' ').title()}")


@router.get("/artwork/{artwork_id}/latest", response_model=APIResponse)
async def get_latest_qa_report(
    artwork_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest QA report for an artwork."""
    result = await db.execute(
        select(QAReport)
        .where(QAReport.artwork_id == artwork_id, QAReport.is_deleted == False)
        .order_by(QAReport.version.desc())
    )
    report = result.scalars().first()
    if not report:
        return APIResponse(data=None, message="No QA report found")
    return APIResponse(data=_report_to_dict(report))


def _report_to_dict(report: QAReport) -> dict:
    return {
        "id": report.id,
        "artwork_id": report.artwork_id,
        "version": report.version,
        "status": report.status,
        "overall_score": report.overall_score,
        "production_ready": report.production_ready,
        "critical_issues": report.critical_issues,
        "warnings_count": report.warnings_count,
        "scores": {
            "similarity": report.similarity_score,
            "print_quality": report.print_quality_score,
            "transparency": report.transparency_score,
            "color": report.color_score,
            "edge": report.edge_score,
        },
        "visual_inspection": json.loads(report.visual_inspection) if report.visual_inspection else None,
        "print_inspection": json.loads(report.print_inspection) if report.print_inspection else None,
        "similarity_validation": json.loads(report.similarity_validation) if report.similarity_validation else None,
        "product_validation": json.loads(report.product_validation) if report.product_validation else None,
        "issues": json.loads(report.issues) if report.issues else [],
        "recommendations": json.loads(report.recommendations) if report.recommendations else [],
        "reviewer_id": report.reviewer_id,
        "reviewed_at": report.reviewed_at.isoformat() if report.reviewed_at else None,
        "approval_notes": report.approval_notes,
    }
