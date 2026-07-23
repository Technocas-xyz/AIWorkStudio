"""Quality Assurance Engine - comprehensive inspection of Master Artwork."""

import io
import json
import math
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.artwork import Artwork
from app.models.generation import MasterArtwork, CandidateArtwork
from app.models.qa import QAReport

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")


class QAEngine:
    """Comprehensive Quality Assurance inspection engine."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_inspection(self, artwork_id: str, user_id: str) -> QAReport:
        """Start a QA inspection for an artwork."""
        # Load artwork
        result = await self.db.execute(select(Artwork).where(Artwork.id == artwork_id, Artwork.is_deleted == False))
        artwork = result.scalar_one_or_none()
        if not artwork:
            raise ValueError("Artwork not found")

        # Check version
        existing = await self.db.execute(
            select(QAReport).where(QAReport.artwork_id == artwork_id, QAReport.is_deleted == False).order_by(QAReport.version.desc())
        )
        last = existing.scalars().first()
        version = (last.version + 1) if last else 1

        # Load master artwork if exists
        master_result = await self.db.execute(
            select(MasterArtwork).where(MasterArtwork.artwork_id == artwork_id, MasterArtwork.is_deleted == False).order_by(MasterArtwork.version.desc())
        )
        master = master_result.scalars().first()

        report = QAReport(
            id=str(uuid.uuid4()),
            artwork_id=artwork_id,
            master_artwork_id=master.id if master else None,
            version=version,
            status="inspecting",
            requested_by_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)
        return report

    async def run_inspection(self, report_id: str) -> Optional[QAReport]:
        """Execute the full QA inspection pipeline."""
        result = await self.db.execute(select(QAReport).where(QAReport.id == report_id))
        report = result.scalar_one_or_none()
        if not report:
            return None

        # Load artwork
        art_result = await self.db.execute(select(Artwork).where(Artwork.id == report.artwork_id))
        artwork = art_result.scalar_one_or_none()
        if not artwork:
            return None

        # Load the file to inspect: generated image (master or latest candidate)
        file_bytes = None
        original_bytes = None

        # Try loading approved Master Artwork first
        if report.master_artwork_id:
            master_result = await self.db.execute(select(MasterArtwork).where(MasterArtwork.id == report.master_artwork_id))
            master = master_result.scalars().first()
            if master:
                master_path = os.path.join(UPLOAD_DIR, master.storage_path)
                if os.path.exists(master_path):
                    with open(master_path, "rb") as f:
                        file_bytes = f.read()

        # If no master, try loading the latest generated candidate
        if not file_bytes:
            from app.models.generation import GenerationJob, CandidateArtwork
            cand_result = await self.db.execute(
                select(CandidateArtwork)
                .join(GenerationJob, GenerationJob.id == CandidateArtwork.job_id)
                .where(GenerationJob.artwork_id == report.artwork_id, CandidateArtwork.is_deleted == False)
                .order_by(CandidateArtwork.created_at.desc())
            )
            latest_candidate = cand_result.scalars().first()
            if latest_candidate:
                cand_path = os.path.join(UPLOAD_DIR, latest_candidate.storage_path)
                if os.path.exists(cand_path):
                    with open(cand_path, "rb") as f:
                        file_bytes = f.read()

        # Load original artwork (for comparison)
        orig_path = os.path.join(UPLOAD_DIR, artwork.storage_bucket, artwork.storage_path)
        if os.path.exists(orig_path):
            with open(orig_path, "rb") as f:
                original_bytes = f.read()

        # If no generated image exists at all, inspect the original itself
        if not file_bytes:
            file_bytes = original_bytes

        if not file_bytes:
            report.status = "completed"
            report.overall_score = 0
            report.issues = json.dumps([{"title": "File Not Found", "severity": "critical", "description": "Could not load artwork file"}])
            await self.db.flush()
            return report

        # Run all inspections on the GENERATED image
        # Get actual properties of the generated file (not from the original artwork record)
        gen_width, gen_height, gen_has_alpha, gen_dpi = self._get_image_properties(file_bytes)

        visual = self._visual_inspection(file_bytes, gen_width, gen_height, gen_has_alpha)
        print_insp = self._print_inspection(file_bytes, gen_width, gen_height, gen_dpi, gen_has_alpha)

        # Similarity: compare generated image against original
        is_generated_different = (file_bytes != original_bytes) if original_bytes else False
        if is_generated_different and original_bytes:
            similarity = self._similarity_validation(original_bytes, file_bytes)
        else:
            # No generated image found — skip similarity (inspecting original itself)
            similarity = {"overall": 0, "subject": 0, "color": 0, "layout": 0, "composition": 0, "note": "No generated image to compare — run AI Production first"}

        product_val = self._product_validation(gen_width, gen_height, gen_has_alpha, gen_dpi)

        # Collect all issues
        all_issues = []
        all_issues.extend(visual.get("issues", []))
        all_issues.extend(print_insp.get("issues", []))
        all_issues.extend(product_val.get("issues", []))

        # Generate recommendations
        recommendations = self._generate_recommendations(all_issues, visual, print_insp)

        # Calculate scores
        scores = self._calculate_scores(visual, print_insp, similarity, product_val)

        # Determine production readiness
        critical_count = sum(1 for i in all_issues if i.get("severity") == "critical")
        warning_count = sum(1 for i in all_issues if i.get("severity") in ("high", "medium"))
        production_ready = critical_count == 0 and scores["overall"] >= 70

        # Update report
        report.status = "completed"
        report.overall_score = scores["overall"]
        report.production_ready = production_ready
        report.critical_issues = critical_count
        report.warnings_count = warning_count
        report.similarity_score = scores["similarity"]
        report.print_quality_score = scores["print"]
        report.transparency_score = scores["transparency"]
        report.color_score = scores["color"]
        report.edge_score = scores["edge"]
        report.visual_inspection = json.dumps(visual)
        report.print_inspection = json.dumps(print_insp)
        report.similarity_validation = json.dumps(similarity)
        report.product_validation = json.dumps(product_val)
        report.issues = json.dumps(all_issues)
        report.recommendations = json.dumps(recommendations)

        await self.db.flush()
        return report

    async def approve(self, report_id: str, user_id: str, notes: str = "") -> bool:
        result = await self.db.execute(select(QAReport).where(QAReport.id == report_id))
        report = result.scalar_one_or_none()
        if not report:
            return False
        report.status = "approved"
        report.reviewer_id = user_id
        report.reviewed_at = datetime.now(timezone.utc)
        report.approval_notes = notes
        await self.db.flush()
        return True

    async def reject(self, report_id: str, user_id: str, notes: str = "") -> bool:
        result = await self.db.execute(select(QAReport).where(QAReport.id == report_id))
        report = result.scalar_one_or_none()
        if not report:
            return False
        report.status = "rejected"
        report.reviewer_id = user_id
        report.reviewed_at = datetime.now(timezone.utc)
        report.approval_notes = notes
        await self.db.flush()
        return True

    async def send_back(self, report_id: str, user_id: str, target: str, notes: str = "") -> bool:
        result = await self.db.execute(select(QAReport).where(QAReport.id == report_id))
        report = result.scalar_one_or_none()
        if not report:
            return False
        report.status = "sent_back"
        report.reviewer_id = user_id
        report.reviewed_at = datetime.now(timezone.utc)
        report.approval_notes = f"[Sent to {target}] {notes}"
        await self.db.flush()
        return True

    def _get_image_properties(self, file_bytes: bytes) -> tuple:
        """Extract actual width, height, has_alpha, dpi from image bytes."""
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(file_bytes))
            width = img.width
            height = img.height
            has_alpha = img.mode in ("RGBA", "LA", "PA")
            dpi_info = img.info.get("dpi")
            dpi = int(dpi_info[0]) if dpi_info and isinstance(dpi_info, tuple) else 72
            img.close()
            return (width, height, has_alpha, dpi)
        except Exception:
            return (0, 0, False, 72)

    def _visual_inspection(self, file_bytes: bytes, width: int, height: int, has_alpha: bool) -> dict:
        """Comprehensive visual quality inspection."""
        result = {"score": 100, "checks": [], "issues": []}
        try:
            from PIL import Image, ImageFilter, ImageStat
            img = Image.open(io.BytesIO(file_bytes))
            gray = img.convert("L")

            # Sharpness
            lap = gray.filter(ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1, offset=128))
            sharpness = ImageStat.Stat(lap).var[0]
            sharp_pass = sharpness > 150
            result["checks"].append({"name": "Sharpness", "pass": sharp_pass, "value": round(sharpness, 1)})
            if not sharp_pass:
                result["issues"].append({"title": "Soft/Blurry Image", "severity": "medium", "description": f"Sharpness {sharpness:.0f} below threshold (150)", "recommendation": "Re-run with edge refinement"})
                result["score"] -= 10

            # Noise
            from PIL import ImageChops
            smoothed = gray.filter(ImageFilter.GaussianBlur(2))
            diff = ImageChops.difference(gray, smoothed)
            noise_val = ImageStat.Stat(diff).mean[0]
            noise_pass = noise_val < 8
            result["checks"].append({"name": "Noise Level", "pass": noise_pass, "value": round(noise_val, 2)})
            if not noise_pass:
                result["issues"].append({"title": "Image Noise", "severity": "low" if noise_val < 12 else "medium", "description": f"Noise level {noise_val:.1f}", "recommendation": "Enable noise reduction"})
                result["score"] -= 5

            # Edge quality (if has alpha)
            if img.mode == "RGBA":
                alpha = img.split()[3]
                alpha_edges = alpha.filter(ImageFilter.FIND_EDGES)
                edge_var = ImageStat.Stat(alpha_edges).var[0]
                edge_pass = edge_var < 4000
                result["checks"].append({"name": "Edge Smoothness", "pass": edge_pass, "value": round(edge_var, 1)})
                if not edge_pass:
                    result["issues"].append({"title": "Jagged Edges", "severity": "medium", "description": "Edge variance too high", "recommendation": "Apply edge refinement"})
                    result["score"] -= 8

                # Halo detection
                dilated = alpha.filter(ImageFilter.MaxFilter(3))
                fringe = ImageChops.difference(dilated, alpha)
                halo_val = ImageStat.Stat(fringe).mean[0]
                halo_pass = halo_val < 8
                result["checks"].append({"name": "No Halos", "pass": halo_pass, "value": round(halo_val, 2)})
                if not halo_pass:
                    result["issues"].append({"title": "Edge Halos Detected", "severity": "medium", "description": f"Halo intensity {halo_val:.1f}", "recommendation": "Enable halo removal in Reconstruction"})
                    result["score"] -= 10

                # Transparency check
                alpha_stat = ImageStat.Stat(alpha)
                result["checks"].append({"name": "Has Transparency", "pass": True, "value": f"{(255 - alpha_stat.mean[0]) / 255 * 100:.1f}% transparent"})
            else:
                result["checks"].append({"name": "Has Transparency", "pass": False, "value": "No alpha channel"})
                result["issues"].append({"title": "No Transparency", "severity": "high", "description": "Image has no alpha channel - required for DTF", "recommendation": "Enable background removal"})
                result["score"] -= 15

            # Contrast
            gray_stat = ImageStat.Stat(gray)
            contrast = math.sqrt(gray_stat.var[0])
            contrast_pass = 30 < contrast < 90
            result["checks"].append({"name": "Contrast", "pass": contrast_pass, "value": round(contrast, 1)})
            if not contrast_pass:
                result["issues"].append({"title": "Contrast Issue", "severity": "low", "description": f"Contrast {contrast:.0f} ({'too low' if contrast <= 30 else 'very high'})", "recommendation": "Review color settings"})
                result["score"] -= 3

            img.close()
        except Exception as e:
            result["issues"].append({"title": "Inspection Error", "severity": "high", "description": str(e)})
            result["score"] -= 20

        result["score"] = max(0, result["score"])
        return result

    def _print_inspection(self, file_bytes: bytes, width: int, height: int, dpi: int, has_alpha: bool) -> dict:
        """Print readiness validation of the generated image."""
        result = {"score": 100, "checks": [], "issues": []}
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(file_bytes))

            # DPI check
            dpi_pass = dpi >= 200
            result["checks"].append({"name": "Minimum DPI (200)", "pass": dpi_pass, "value": dpi})
            if not dpi_pass:
                result["issues"].append({"title": "DPI Below Minimum", "severity": "critical", "description": f"{dpi} DPI < 200 minimum", "recommendation": "Apply AI upscaling"})
                result["score"] -= 25

            dpi_optimal = dpi >= 300
            result["checks"].append({"name": "Optimal DPI (300)", "pass": dpi_optimal, "value": dpi})
            if not dpi_optimal and dpi_pass:
                result["score"] -= 5

            # Resolution
            res_pass = width >= 1000 and height >= 1000
            result["checks"].append({"name": "Minimum Resolution", "pass": res_pass, "value": f"{width}×{height}"})
            if not res_pass:
                result["issues"].append({"title": "Low Resolution", "severity": "high", "description": f"{width}×{height} may be too small for production", "recommendation": "Apply super resolution"})
                result["score"] -= 15

            # Bit depth
            mode_bits = {"RGB": 24, "RGBA": 32, "L": 8, "P": 8, "CMYK": 32}
            bit_depth = mode_bits.get(img.mode, 8)
            bit_pass = bit_depth >= 24
            result["checks"].append({"name": "Bit Depth (24+)", "pass": bit_pass, "value": f"{bit_depth}-bit ({img.mode})"})

            # Print size at 300 DPI
            print_w = width / 300
            print_h = height / 300
            result["checks"].append({"name": "Print Size @300dpi", "pass": True, "value": f"{print_w:.1f}\" × {print_h:.1f}\""})

            # Safe margins
            if has_alpha and img.mode == "RGBA":
                alpha = img.split()[3]
                bbox = alpha.getbbox()
                if bbox:
                    margin_t = bbox[1]
                    margin_l = bbox[0]
                    margin_r = width - bbox[2]
                    margin_b = height - bbox[3]
                    margin_pass = all(m >= 5 for m in [margin_t, margin_l, margin_r, margin_b])
                    result["checks"].append({"name": "Safe Margins", "pass": margin_pass, "value": f"T:{margin_t} L:{margin_l} R:{margin_r} B:{margin_b}"})
                    if not margin_pass:
                        result["issues"].append({"title": "Tight Margins", "severity": "low", "description": "Subject very close to edge", "recommendation": "Consider canvas expansion"})
                        result["score"] -= 3

            # Transparency check
            result["checks"].append({"name": "Has Transparency", "pass": has_alpha, "value": "Yes" if has_alpha else "No"})
            if not has_alpha:
                result["issues"].append({"title": "No Transparency", "severity": "high", "description": "Generated image has no alpha channel", "recommendation": "Enable background removal"})
                result["score"] -= 10

            img.close()
        except Exception as e:
            result["issues"].append({"title": "Print Inspection Error", "severity": "high", "description": str(e)})
            result["score"] -= 20

        result["score"] = max(0, result["score"])
        return result

    def _similarity_validation(self, original: bytes, generated: bytes) -> dict:
        """Compare original vs generated artwork."""
        try:
            from PIL import Image, ImageStat, ImageChops
            orig = Image.open(io.BytesIO(original)).convert("RGB").resize((256, 256))
            gen = Image.open(io.BytesIO(generated)).convert("RGB").resize((256, 256))

            # Color similarity
            orig_stat = ImageStat.Stat(orig)
            gen_stat = ImageStat.Stat(gen)
            color_diff = sum(abs(a - b) for a, b in zip(orig_stat.mean, gen_stat.mean)) / (3 * 255)
            color_score = round((1 - color_diff) * 100, 1)

            # Pixel similarity
            diff = ImageChops.difference(orig, gen)
            diff_stat = ImageStat.Stat(diff)
            pixel_diff = sum(diff_stat.mean) / (3 * 255)
            subject_score = round((1 - pixel_diff) * 100, 1)

            # Histogram
            h1, h2 = orig.histogram(), gen.histogram()
            hist_sim = sum(min(a, b) for a, b in zip(h1, h2)) / max(sum(h1), 1)
            layout_score = round(hist_sim * 100, 1)

            overall = round((subject_score * 0.4 + color_score * 0.3 + layout_score * 0.3), 1)

            orig.close()
            gen.close()
            return {"overall": overall, "subject": subject_score, "color": color_score, "layout": layout_score, "composition": overall}
        except Exception:
            return {"overall": 100, "subject": 100, "color": 100, "layout": 100, "composition": 100}

    def _product_validation(self, width: int, height: int, has_alpha: bool, dpi: int) -> dict:
        """Validate generated image against DTF product rules."""
        result = {"product": "DTF Transfer", "checks": [], "issues": [], "pass": True}

        result["checks"].append({"name": "Transparent Background", "pass": has_alpha})
        if not has_alpha:
            result["issues"].append({"title": "No Transparency for DTF", "severity": "critical", "description": "DTF requires transparent background", "recommendation": "Apply background removal"})
            result["pass"] = False

        result["checks"].append({"name": "DPI ≥ 200", "pass": dpi >= 200})
        result["checks"].append({"name": "DPI ≥ 300 (optimal)", "pass": dpi >= 300})

        size_ok = width >= 500 and height >= 500
        result["checks"].append({"name": "Minimum Dimensions", "pass": size_ok})

        return result

    def _generate_recommendations(self, issues: list, visual: dict, print_insp: dict) -> list:
        recs = []
        severity_map = {i["title"]: i.get("recommendation", "") for i in issues if i.get("recommendation")}

        for title, rec_text in severity_map.items():
            module = "Reconstruction"
            if "DPI" in title or "resolution" in title.lower():
                module = "Reconstruction"
            elif "background" in title.lower() or "transparency" in title.lower():
                module = "Reconstruction"
            elif "halo" in title.lower() or "edge" in title.lower():
                module = "AI Production"
            recs.append({"action": rec_text, "module": module, "issue": title})

        return recs

    def _calculate_scores(self, visual: dict, print_insp: dict, similarity: dict, product: dict) -> dict:
        sim_score = similarity.get("overall", 100)
        print_score = print_insp.get("score", 100)
        visual_score = visual.get("score", 100)

        # Weighted
        overall = round(sim_score * 0.25 + print_score * 0.25 + visual_score * 0.2 + sim_score * 0.15 + visual_score * 0.15, 1)

        return {
            "overall": min(100, max(0, overall)),
            "similarity": sim_score,
            "print": print_score,
            "transparency": 100 if product.get("pass") else 50,
            "color": similarity.get("color", 100),
            "edge": visual_score,
        }
