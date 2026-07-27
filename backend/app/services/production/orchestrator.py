"""AI Orchestrator - central coordination layer for generation pipeline."""

import json
import os
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.artwork import Artwork
from app.models.analysis import AnalysisJob, AnalysisReport
from app.models.generation import GenerationJob, CandidateArtwork, MasterArtwork
from app.services.production.prompt_builder import PromptBuilder
from app.services.production.model_registry import get_model_adapter, list_models
from app.services.production.post_processor import PostProcessor
from app.services.production.similarity_validator import SimilarityValidator

# Upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")


class ProductionOrchestrator:
    """Coordinates the full AI generation pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.prompt_builder = PromptBuilder()
        self.post_processor = PostProcessor()
        self.similarity_validator = SimilarityValidator()

    async def start_generation(self, artwork_id: str, user_id: str,
                                model_name: str = "gpt_image",
                                mode: str = "enhancement") -> GenerationJob:
        """Create and start a generation job."""
        # Load artwork
        result = await self.db.execute(
            select(Artwork).where(Artwork.id == artwork_id, Artwork.is_deleted == False)
        )
        artwork = result.scalar_one_or_none()
        if not artwork:
            raise ValueError("Artwork not found")

        # Load latest analysis report
        report_result = await self.db.execute(
            select(AnalysisReport)
            .where(AnalysisReport.artwork_id == artwork_id, AnalysisReport.is_deleted == False)
            .order_by(AnalysisReport.version.desc())
        )
        report = report_result.scalars().first()

        generation_plan = json.loads(report.generation_plan) if report and report.generation_plan else {}

        # Create job
        job = GenerationJob(
            id=str(uuid.uuid4()),
            artwork_id=artwork_id,
            analysis_job_id=report.job_id if report else None,
            model_name=model_name,
            mode=mode,
            status="pending",
            current_step="initializing",
            progress=0,
            generation_plan=json.dumps(generation_plan),
            requested_by_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def run_generation(self, job_id: str, operations: dict = None,
                             custom_instructions: str = "", target_ratio: str = "") -> Optional[CandidateArtwork]:
        """Execute the full generation pipeline."""
        # Load job
        result = await self.db.execute(select(GenerationJob).where(GenerationJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return None

        # Load artwork
        result = await self.db.execute(select(Artwork).where(Artwork.id == job.artwork_id))
        artwork = result.scalar_one_or_none()
        if not artwork:
            job.status = "failed"
            job.error_message = "Artwork not found"
            await self.db.flush()
            return None

        job.status = "generating"
        job.started_at = datetime.utcnow()
        await self.db.flush()

        try:
            generation_plan = json.loads(job.generation_plan) if job.generation_plan else {}

            # Step 1: Build Prompt
            job.current_step = "building_prompt"
            job.progress = 10
            await self.db.flush()

            # Load visual analysis from latest report for detailed prompt
            visual_analysis_data = {}
            if report and report.visual_analysis:
                try:
                    visual_analysis_data = json.loads(report.visual_analysis)
                except Exception:
                    pass

            prompt = self.prompt_builder.build_prompt(
                generation_plan,
                mode=job.mode,
                operations=operations or {},
                custom_instructions=custom_instructions,
                target_ratio=target_ratio,
                visual_analysis=visual_analysis_data,
            )
            job.prompt_used = prompt

            # Step 2: Load reference image
            job.current_step = "loading_reference"
            job.progress = 20
            await self.db.flush()

            reference_bytes = self._load_artwork_file(artwork)

            # Step 3: Generate via AI model
            job.current_step = "generating"
            job.progress = 30
            await self.db.flush()

            adapter = get_model_adapter(job.model_name)
            if not adapter.is_available():
                raise RuntimeError(f"Model '{job.model_name}' is not available (check API key)")

            generated_bytes = await adapter.generate(
                prompt=prompt,
                reference_image=reference_bytes,
                width=artwork.width or 1024,
                height=artwork.height or 1024,
            )

            if not generated_bytes:
                raise RuntimeError("AI model returned empty result")

            # Step 4: Post Processing
            job.current_step = "post_processing"
            job.progress = 60
            await self.db.flush()

            processed_bytes = self.post_processor.process(generated_bytes, generation_plan)

            # Step 5: Save candidate
            job.current_step = "saving"
            job.progress = 75
            await self.db.flush()

            candidate_path = self._save_candidate(job.id, processed_bytes)

            # Step 6: Similarity Validation
            job.current_step = "validating"
            job.progress = 85
            await self.db.flush()

            similarity_score = self.similarity_validator.compare(reference_bytes, processed_bytes) if reference_bytes else 0.5
            quality_score = self.similarity_validator.assess_quality(processed_bytes)

            # Step 7: Create candidate record
            job.current_step = "finalizing"
            job.progress = 95
            await self.db.flush()

            # Get dimensions of generated image
            gen_width, gen_height = self._get_dimensions(processed_bytes)

            candidate_count = await self._get_candidate_count(job.id)

            candidate = CandidateArtwork(
                id=str(uuid.uuid4()),
                job_id=job.id,
                artwork_id=artwork.id,
                candidate_number=candidate_count + 1,
                model_name=job.model_name,
                storage_path=candidate_path,
                file_size=len(processed_bytes),
                width=gen_width,
                height=gen_height,
                similarity_score=round(similarity_score * 100, 1),
                quality_score=round(quality_score * 100, 1),
                status="generated",
                post_processed=True,
                metadata_json=json.dumps({
                    "mode": job.mode,
                    "prompt_length": len(prompt),
                    "model": job.model_name,
                }),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(candidate)

            # Complete job
            job.status = "completed"
            job.current_step = "completed"
            job.progress = 100
            job.completed_at = datetime.utcnow()
            if job.started_at:
                job.duration_seconds = (job.completed_at - job.started_at).total_seconds()

            await self.db.flush()
            return candidate

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.current_step = "failed"
            job.retry_count += 1
            await self.db.flush()
            return None

    async def approve_candidate(self, candidate_id: str, user_id: str) -> Optional[MasterArtwork]:
        """Approve a candidate as Master Artwork."""
        result = await self.db.execute(select(CandidateArtwork).where(CandidateArtwork.id == candidate_id))
        candidate = result.scalar_one_or_none()
        if not candidate:
            return None

        candidate.status = "approved"

        # Check existing master versions
        existing = await self.db.execute(
            select(MasterArtwork)
            .where(MasterArtwork.artwork_id == candidate.artwork_id, MasterArtwork.is_deleted == False)
            .order_by(MasterArtwork.version.desc())
        )
        last_master = existing.scalars().first()
        version = (last_master.version + 1) if last_master else 1

        master = MasterArtwork(
            id=str(uuid.uuid4()),
            artwork_id=candidate.artwork_id,
            candidate_id=candidate.id,
            job_id=candidate.job_id,
            version=version,
            model_name=candidate.model_name,
            similarity_score=candidate.similarity_score,
            quality_score=candidate.quality_score,
            production_score=(candidate.similarity_score + candidate.quality_score) / 2 if candidate.similarity_score and candidate.quality_score else None,
            storage_path=candidate.storage_path,
            approved_by_id=user_id,
            approved_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(master)
        await self.db.flush()
        return master

    async def reject_candidate(self, candidate_id: str) -> bool:
        result = await self.db.execute(select(CandidateArtwork).where(CandidateArtwork.id == candidate_id))
        candidate = result.scalar_one_or_none()
        if not candidate:
            return False
        candidate.status = "rejected"
        await self.db.flush()
        return True

    async def get_job(self, job_id: str) -> Optional[GenerationJob]:
        result = await self.db.execute(select(GenerationJob).where(GenerationJob.id == job_id))
        return result.scalar_one_or_none()

    async def get_candidates(self, job_id: str) -> list:
        result = await self.db.execute(
            select(CandidateArtwork)
            .where(CandidateArtwork.job_id == job_id, CandidateArtwork.is_deleted == False)
            .order_by(CandidateArtwork.candidate_number)
        )
        return list(result.scalars().all())

    async def get_master_artwork(self, artwork_id: str) -> Optional[MasterArtwork]:
        result = await self.db.execute(
            select(MasterArtwork)
            .where(MasterArtwork.artwork_id == artwork_id, MasterArtwork.is_deleted == False)
            .order_by(MasterArtwork.version.desc())
        )
        return result.scalars().first()

    async def _get_candidate_count(self, job_id: str) -> int:
        result = await self.db.execute(
            select(CandidateArtwork).where(CandidateArtwork.job_id == job_id)
        )
        return len(list(result.scalars().all()))

    def _load_artwork_file(self, artwork: Artwork) -> Optional[bytes]:
        file_path = os.path.join(UPLOAD_DIR, artwork.storage_bucket, artwork.storage_path)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                return f.read()
        return None

    def _save_candidate(self, job_id: str, image_bytes: bytes) -> str:
        dir_path = os.path.join(UPLOAD_DIR, "generations", job_id)
        os.makedirs(dir_path, exist_ok=True)
        filename = f"{uuid.uuid4()}.png"
        file_path = os.path.join(dir_path, filename)
        with open(file_path, "wb") as f:
            f.write(image_bytes)
        return f"generations/{job_id}/{filename}"

    def _get_dimensions(self, image_bytes: bytes) -> tuple:
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(image_bytes))
            dims = (img.width, img.height)
            img.close()
            return dims
        except Exception:
            return (0, 0)
