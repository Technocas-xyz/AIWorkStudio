"""Generation models for Module 4 - AI Production Studio."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class AIModel(BaseModel):
    __tablename__ = "ai_models"

    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    provider = Column(String(100), nullable=False)
    model_id = Column(String(200), nullable=False)
    api_endpoint = Column(String(500), nullable=True)
    supported_features = Column(Text, nullable=True)  # JSON list
    max_resolution = Column(Integer, default=4096, nullable=False)
    cost_per_generation = Column(Float, default=0.0, nullable=False)
    queue_priority = Column(Integer, default=5, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    config = Column(Text, nullable=True)  # JSON config


class PromptTemplate(BaseModel):
    __tablename__ = "prompt_templates"

    name = Column(String(200), nullable=False)
    model_name = Column(String(100), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    template_text = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    variables = Column(Text, nullable=True)  # JSON list of variable names
    is_active = Column(Boolean, default=True, nullable=False)


class GenerationJob(BaseModel):
    __tablename__ = "generation_jobs"

    artwork_id = Column(String(36), ForeignKey("artworks.id"), nullable=False, index=True)
    analysis_job_id = Column(String(36), ForeignKey("analysis_jobs.id"), nullable=True)
    model_name = Column(String(100), nullable=False)
    mode = Column(String(50), default="enhancement", nullable=False)  # reconstruction, enhancement, upscaling, background_cleanup, edge_refinement, production_cleanup
    status = Column(String(30), default="pending", nullable=False, index=True)  # pending, generating, post_processing, validating, completed, failed, cancelled
    progress = Column(Integer, default=0, nullable=False)
    current_step = Column(String(50), nullable=True)
    prompt_used = Column(Text, nullable=True)
    prompt_template_id = Column(String(36), nullable=True)
    generation_plan = Column(Text, nullable=True)  # JSON
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    requested_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Relationships
    artwork = relationship("Artwork")
    requested_by = relationship("User")
    candidates = relationship("CandidateArtwork", back_populates="job", order_by="CandidateArtwork.created_at")


class CandidateArtwork(BaseModel):
    __tablename__ = "candidate_artworks"

    job_id = Column(String(36), ForeignKey("generation_jobs.id"), nullable=False, index=True)
    artwork_id = Column(String(36), ForeignKey("artworks.id"), nullable=False)
    candidate_number = Column(Integer, nullable=False)
    model_name = Column(String(100), nullable=False)
    storage_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, default=0, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    similarity_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    status = Column(String(30), default="generated", nullable=False)  # generated, approved, rejected
    post_processed = Column(Boolean, default=False, nullable=False)
    metadata_json = Column(Text, nullable=True)

    # Relationships
    job = relationship("GenerationJob", back_populates="candidates")
    artwork = relationship("Artwork")


class MasterArtwork(BaseModel):
    __tablename__ = "master_artworks"

    artwork_id = Column(String(36), ForeignKey("artworks.id"), nullable=False, index=True)
    candidate_id = Column(String(36), ForeignKey("candidate_artworks.id"), nullable=False)
    job_id = Column(String(36), ForeignKey("generation_jobs.id"), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    model_name = Column(String(100), nullable=False)
    similarity_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    production_score = Column(Float, nullable=True)
    storage_path = Column(String(1000), nullable=False)
    approved_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    artwork = relationship("Artwork")
    candidate = relationship("CandidateArtwork")
    approved_by = relationship("User")
