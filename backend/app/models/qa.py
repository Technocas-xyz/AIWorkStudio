"""Quality Assurance models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class QAReport(BaseModel):
    __tablename__ = "qa_reports"

    artwork_id = Column(String(36), ForeignKey("artworks.id"), nullable=False, index=True)
    master_artwork_id = Column(String(36), ForeignKey("master_artworks.id"), nullable=True)
    version = Column(Integer, default=1, nullable=False)
    status = Column(String(30), default="inspecting", nullable=False)  # inspecting, completed, approved, rejected, sent_back
    overall_score = Column(Float, nullable=True)
    production_ready = Column(Boolean, default=False, nullable=False)
    critical_issues = Column(Integer, default=0, nullable=False)
    warnings_count = Column(Integer, default=0, nullable=False)
    similarity_score = Column(Float, nullable=True)
    print_quality_score = Column(Float, nullable=True)
    transparency_score = Column(Float, nullable=True)
    color_score = Column(Float, nullable=True)
    edge_score = Column(Float, nullable=True)
    # Full inspection data (JSON)
    visual_inspection = Column(Text, nullable=True)
    print_inspection = Column(Text, nullable=True)
    similarity_validation = Column(Text, nullable=True)
    product_validation = Column(Text, nullable=True)
    issues = Column(Text, nullable=True)  # JSON array
    recommendations = Column(Text, nullable=True)  # JSON array
    # Approval
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    approval_notes = Column(Text, nullable=True)
    requested_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    artwork = relationship("Artwork")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    requested_by = relationship("User", foreign_keys=[requested_by_id])
