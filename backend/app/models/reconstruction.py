"""Reconstruction and Production Planning models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ReconstructionPlan(BaseModel):
    __tablename__ = "reconstruction_plans"

    artwork_id = Column(String(36), ForeignKey("artworks.id"), nullable=False, index=True)
    analysis_job_id = Column(String(36), ForeignKey("analysis_jobs.id"), nullable=True)
    status = Column(String(30), default="draft", nullable=False)  # draft, validated, approved, executing
    strategy_summary = Column(Text, nullable=True)  # JSON
    operations = Column(Text, nullable=True)  # JSON array of operations
    ai_model_primary = Column(String(100), default="gpt_image", nullable=False)
    ai_model_fallback = Column(String(100), nullable=True)
    estimated_time_seconds = Column(Integer, nullable=True)
    estimated_credits = Column(Float, nullable=True)
    estimated_quality_score = Column(Integer, nullable=True)
    estimated_similarity = Column(Float, nullable=True)
    target_width = Column(Integer, nullable=True)
    target_height = Column(Integer, nullable=True)
    target_dpi = Column(Integer, default=300, nullable=False)
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    approved_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    artwork = relationship("Artwork")
    created_by = relationship("User", foreign_keys=[created_by_id])


class ProductProfile(BaseModel):
    __tablename__ = "product_profiles"

    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)  # apparel, transfer, print, accessory
    max_width = Column(Float, nullable=False)  # inches
    max_height = Column(Float, nullable=False)
    min_dpi = Column(Integer, default=200, nullable=False)
    recommended_dpi = Column(Integer, default=300, nullable=False)
    requires_transparency = Column(Boolean, default=True, nullable=False)
    requires_bleed = Column(Boolean, default=False, nullable=False)
    bleed_size = Column(Float, default=0, nullable=False)  # inches
    color_profile = Column(String(50), default="sRGB", nullable=False)
    output_format = Column(String(10), default="PNG", nullable=False)
    rules = Column(Text, nullable=True)  # JSON
    is_active = Column(Boolean, default=True, nullable=False)


class ProductionPlan(BaseModel):
    __tablename__ = "production_plans"

    artwork_id = Column(String(36), ForeignKey("artworks.id"), nullable=False, index=True)
    reconstruction_plan_id = Column(String(36), ForeignKey("reconstruction_plans.id"), nullable=True)
    product_name = Column(String(100), nullable=False)
    status = Column(String(30), default="draft", nullable=False)  # draft, validated, approved
    print_width = Column(Float, nullable=True)  # inches
    print_height = Column(Float, nullable=True)
    target_dpi = Column(Integer, default=300, nullable=False)
    aspect_ratio = Column(String(20), nullable=True)
    orientation = Column(String(20), nullable=True)
    placement = Column(String(50), nullable=True)  # center, left_chest, full_back, etc.
    scale_factor = Column(Float, default=1.0, nullable=False)
    requires_bleed = Column(Boolean, default=False, nullable=False)
    output_format = Column(String(10), default="PNG", nullable=False)
    color_profile = Column(String(50), default="sRGB", nullable=False)
    warnings = Column(Text, nullable=True)  # JSON
    specifications = Column(Text, nullable=True)  # JSON
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    artwork = relationship("Artwork")
    created_by = relationship("User")
