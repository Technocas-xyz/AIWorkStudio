"""Analysis Orchestrator - coordinates all intelligence engines."""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.analysis import AnalysisJob, AnalysisReport
from app.models.artwork import Artwork
from app.services.intelligence.file_inspector import FileInspector
from app.services.intelligence.visual_analyzer import VisualAnalyzer
from app.services.intelligence.gpt_visual_analyzer import GPTVisualAnalyzer
from app.services.intelligence.geometry_engine import GeometryEngine
from app.services.intelligence.production_analyzer import ProductionAnalyzer
from app.services.intelligence.product_intelligence import ProductIntelligence
from app.services.intelligence.risk_assessor import RiskAssessor
from app.services.intelligence.decision_engine import DecisionEngine
from app.services.intelligence.plan_builder import PlanBuilder
from app.services.intelligence.aspect_ratio_analyzer import AspectRatioAnalyzer
from app.services.intelligence.recommendation_engine import RecommendationEngine
from app.services.intelligence.image_quality_analyzer import ImageQualityAnalyzer


class AnalysisOrchestrator:
    """Coordinates the full analysis pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.file_inspector = FileInspector()
        self.visual_analyzer = VisualAnalyzer()
        self.gpt_visual_analyzer = GPTVisualAnalyzer()
        self.geometry_engine = GeometryEngine()
        self.production_analyzer = ProductionAnalyzer()
        self.product_intelligence = ProductIntelligence()
        self.risk_assessor = RiskAssessor()
        self.decision_engine = DecisionEngine()
        self.plan_builder = PlanBuilder()
        self.aspect_ratio_analyzer = AspectRatioAnalyzer()
        self.recommendation_engine = RecommendationEngine()
        self.image_quality_analyzer = ImageQualityAnalyzer()

    async def start_analysis(self, artwork_id: str, user_id: str, engine: str = "pillow") -> AnalysisJob:
        """Create and start an analysis job."""
        # Get artwork
        result = await self.db.execute(
            select(Artwork).where(Artwork.id == artwork_id, Artwork.is_deleted == False)
        )
        artwork = result.scalar_one_or_none()
        if not artwork:
            raise ValueError("Artwork not found")

        # Check for existing version
        existing = await self.db.execute(
            select(AnalysisJob).where(
                AnalysisJob.artwork_id == artwork_id,
                AnalysisJob.is_deleted == False,
            ).order_by(AnalysisJob.version.desc())
        )
        last_job = existing.scalars().first()
        version = (last_job.version + 1) if last_job else 1

        # Create job
        job = AnalysisJob(
            id=str(uuid.uuid4()),
            artwork_id=artwork_id,
            status="pending",
            current_step="queued",
            progress=0,
            requested_by_id=user_id,
            version=version,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)

        # Store engine choice on the job for the runner
        job._engine = engine
        return job

    async def run_analysis(self, job_id: str, engine: str = "pillow") -> Optional[AnalysisReport]:
        """Execute the full analysis pipeline synchronously."""
        # Load job
        result = await self.db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
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

        # Update status
        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        await self.db.flush()

        try:
            # Load file bytes
            file_bytes = self._load_artwork_file(artwork)
            if not file_bytes:
                raise Exception("Could not read artwork file")

            width = artwork.width or 0
            height = artwork.height or 0
            dpi = artwork.resolution_dpi or 72
            has_alpha = artwork.has_alpha_channel or False
            extension = artwork.extension or ""

            # Step 1: File Inspection
            job.current_step = "file_inspection"
            job.progress = 10
            await self.db.flush()
            file_inspection = self.file_inspector.inspect(file_bytes, artwork.filename, extension)

            # Step 2: Visual Analysis
            job.current_step = "visual_analysis"
            job.progress = 25
            await self.db.flush()

            # Always run Pillow first to get technical data
            pillow_analysis = self.visual_analyzer.analyze(file_bytes, extension, {"width": width, "height": height})

            if engine == "gpt" and self.gpt_visual_analyzer.is_available():
                # Pass Pillow's technical findings to GPT for better-informed analysis
                pillow_context = {
                    "width": width,
                    "height": height,
                    "dpi": dpi,
                    "has_alpha": has_alpha,
                    "color_space": artwork.color_space,
                    "extension": extension,
                    "file_size": artwork.file_size,
                    "pillow_color_analysis": pillow_analysis.get("color_analysis", {}),
                    "pillow_background": pillow_analysis.get("background", {}),
                    "pillow_composition": pillow_analysis.get("composition", {}),
                    "pillow_artwork_type": pillow_analysis.get("artwork_type"),
                    "pillow_artistic_style": pillow_analysis.get("artistic_style"),
                }
                visual_analysis = self.gpt_visual_analyzer.analyze(file_bytes, extension, pillow_context)
            else:
                visual_analysis = pillow_analysis

            # Tag which engine was used
            visual_analysis["engine_used"] = engine if (engine == "gpt" and self.gpt_visual_analyzer.is_available()) else "pillow"

            # Step 3: Geometry Analysis
            job.current_step = "geometry_analysis"
            job.progress = 40
            await self.db.flush()
            geometry_analysis = self.geometry_engine.analyze(file_bytes, extension, width, height, has_alpha)

            # Step 3b: Aspect Ratio Analysis
            job.current_step = "aspect_ratio_analysis"
            job.progress = 47
            await self.db.flush()
            aspect_ratio_analysis = self.aspect_ratio_analyzer.analyze(
                width, height, has_alpha,
                geometry_analysis.get("subject_coverage_pct", 100),
                geometry_analysis.get("edge_contact", {}),
                geometry_analysis.get("bounding_box", {}),
            )
            # Attach to geometry for unified access
            geometry_analysis["aspect_ratio"] = aspect_ratio_analysis

            # Step 3c: Image Quality Analysis
            job.current_step = "image_quality_analysis"
            job.progress = 50
            await self.db.flush()
            image_quality = self.image_quality_analyzer.analyze(file_bytes, extension, width, height, has_alpha)

            # Step 4: Production Analysis
            job.current_step = "production_analysis"
            job.progress = 55
            await self.db.flush()
            production_analysis = self.production_analyzer.analyze(
                width, height, dpi, extension, artwork.color_space,
                has_alpha, artwork.file_size, geometry_analysis, visual_analysis
            )

            # Step 5: Product Intelligence
            job.current_step = "product_analysis"
            job.progress = 70
            await self.db.flush()
            product_compat = self.product_intelligence.analyze(
                width, height, dpi, has_alpha,
                visual_analysis.get("color_analysis", {}).get("color_complexity", "medium"),
                visual_analysis.get("artwork_type", "unknown"),
                production_analysis.get("production_score", 50),
            )

            # Step 6: Risk Assessment
            job.current_step = "risk_assessment"
            job.progress = 82
            await self.db.flush()
            risk_assessment = self.risk_assessor.assess(
                file_inspection, visual_analysis, geometry_analysis,
                production_analysis, width, height, dpi, has_alpha
            )

            # Step 7: Decision Engine
            job.current_step = "decision_engine"
            job.progress = 90
            await self.db.flush()
            decisions = self.decision_engine.decide(
                file_inspection, visual_analysis, geometry_analysis,
                production_analysis, risk_assessment, width, height,
                dpi, has_alpha, extension
            )

            # Step 8: Generation Plan
            job.current_step = "generation_plan"
            job.progress = 95
            await self.db.flush()
            generation_plan = self.plan_builder.build(
                analysis_id=job.id,
                artwork_id=artwork.id,
                artwork_ext=extension,
                file_inspection=file_inspection,
                visual=visual_analysis,
                geometry=geometry_analysis,
                production=production_analysis,
                products=product_compat,
                risks=risk_assessment,
                decisions=decisions,
            )

            # Create report
            # Attach image quality to production analysis for storage
            production_analysis["image_quality"] = image_quality

            report = AnalysisReport(
                id=str(uuid.uuid4()),
                job_id=job.id,
                artwork_id=artwork.id,
                version=job.version,
                file_inspection=json.dumps(file_inspection),
                visual_analysis=json.dumps(visual_analysis),
                geometry_analysis=json.dumps(geometry_analysis),
                production_analysis=json.dumps(production_analysis),
                product_compatibility=json.dumps(product_compat),
                risk_assessment=json.dumps(risk_assessment),
                decision_plan=json.dumps(decisions),
                generation_plan=json.dumps(generation_plan),
                overall_score=generation_plan.get("overall_score"),
                risk_level=risk_assessment.get("risk_level"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(report)

            # Complete job
            job.status = "completed"
            job.current_step = "completed"
            job.progress = 100
            job.completed_at = datetime.now(timezone.utc)
            if job.started_at:
                job.duration_seconds = (job.completed_at - job.started_at).total_seconds()

            await self.db.flush()
            return report

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.current_step = "failed"
            await self.db.flush()
            return None

    async def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        result = await self.db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
        return result.scalar_one_or_none()

    async def get_report(self, job_id: str) -> Optional[AnalysisReport]:
        result = await self.db.execute(select(AnalysisReport).where(AnalysisReport.job_id == job_id))
        return result.scalar_one_or_none()

    async def get_latest_report_for_artwork(self, artwork_id: str) -> Optional[AnalysisReport]:
        result = await self.db.execute(
            select(AnalysisReport)
            .where(AnalysisReport.artwork_id == artwork_id, AnalysisReport.is_deleted == False)
            .order_by(AnalysisReport.version.desc())
        )
        return result.scalars().first()

    def _load_artwork_file(self, artwork: Artwork) -> Optional[bytes]:
        """Load artwork file bytes from local storage."""
        # Resolve upload directory (same as artworks endpoint)
        base_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "uploads"
        )
        file_path = os.path.join(base_dir, artwork.storage_bucket, artwork.storage_path)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                return f.read()
        return None
