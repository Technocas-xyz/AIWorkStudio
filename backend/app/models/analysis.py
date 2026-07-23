"""Analysis models for the Artwork Intelligence Engine."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class AnalysisJob(BaseModel):
    __tablename__ = "analysis_jobs"

    artwork_id = Column(String(36), ForeignKey("artworks.id"), nullable=False, index=True)
    status = Column(String(30), default="pending", nullable=False, index=True)  # pending, processing, completed, failed
    current_step = Column(String(50), nullable=True)
    progress = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    requested_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    artwork = relationship("Artwork")
    requested_by = relationship("User")
    report = relationship("AnalysisReport", back_populates="job", uselist=False)


class AnalysisReport(BaseModel):
    __tablename__ = "analysis_reports"

    job_id = Column(String(36), ForeignKey("analysis_jobs.id"), nullable=False, unique=True)
    artwork_id = Column(String(36), ForeignKey("artworks.id"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)

    # File Inspection
    file_inspection = Column(Text, nullable=True)  # JSON

    # Visual Analysis
    visual_analysis = Column(Text, nullable=True)  # JSON

    # Geometry Analysis
    geometry_analysis = Column(Text, nullable=True)  # JSON

    # Production Analysis
    production_analysis = Column(Text, nullable=True)  # JSON

    # Product Compatibility
    product_compatibility = Column(Text, nullable=True)  # JSON

    # Risk Assessment
    risk_assessment = Column(Text, nullable=True)  # JSON

    # Decision Plan
    decision_plan = Column(Text, nullable=True)  # JSON

    # Generation Plan (final output)
    generation_plan = Column(Text, nullable=True)  # JSON

    # Overall scores
    overall_score = Column(Integer, nullable=True)
    risk_level = Column(String(20), nullable=True)

    # Relationships
    job = relationship("AnalysisJob", back_populates="report")
    artwork = relationship("Artwork")
