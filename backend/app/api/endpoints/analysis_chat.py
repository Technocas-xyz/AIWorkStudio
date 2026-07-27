"""Analysis Chat endpoint - chat with GPT about a specific analysis report."""

import json
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from app.database import get_db
from app.schemas.common import APIResponse
from app.api.deps import get_current_user
from app.models.user import User
from app.models.analysis import AnalysisReport

# Load API key
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv(os.path.join(_root, ".env"))

router = APIRouter()


class ChatMessage(BaseModel):
    job_id: str = Field(..., description="The analysis job ID to chat about")
    message: str = Field(..., min_length=1, max_length=2000, description="User question")
    history: list = Field(default_factory=list, description="Previous messages for context")
    file_data: Optional[str] = Field(None, description="Base64 encoded file data")
    file_name: Optional[str] = Field(None, description="Attached file name")


# System prompt that restricts GPT to only discuss the analysis
SYSTEM_PROMPT = """You are an expert DTF (Direct-to-Film) production analyst assistant. You can ONLY discuss the analysis report provided below. 

RULES:
1. You can ONLY answer questions about THIS specific artwork analysis and its results.
2. You MUST NOT generate, create, or describe any images.
3. You MUST NOT help with unrelated topics. Politely redirect to the analysis.
4. You explain WHY specific scores, metrics, and issues were detected.
5. You provide actionable advice for improving the artwork for DTF printing.
6. You reference specific numbers from the analysis when answering.
7. Keep answers concise and production-focused.
8. If asked about something outside this analysis, say: "I can only discuss the analysis results for this specific artwork."

You are a print production expert who understands:
- DPI requirements (minimum 200, recommended 300 for DTF)
- Halftone detection (scanned sources cause moirÃ©)
- Blackout areas (heavy ink usage risks on fabric)
- Image noise and its impact on print quality
- JPEG artifacts and why they matter for production
- Color management, contrast, saturation
- Edge quality, halos, fringing
- Aspect ratios and DTF print sizing (max 20" Ã— 28")
- Background removal requirements for garment printing
"""


@router.post("/chat", response_model=APIResponse)
async def analysis_chat(
    body: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Chat with GPT about a specific analysis report. Restricted to analysis context only."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key or api_key == "your-openai-api-key-here":
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")

    # Load the report
    result = await db.execute(select(AnalysisReport).where(AnalysisReport.job_id == body.job_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Analysis report not found")

    # Build context from the report
    report_context = _build_report_context(report)

    # Build messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\n--- ANALYSIS REPORT DATA ---\n" + report_context},
    ]

    # Add history (limit to last 10 messages)
    for msg in body.history[-10:]:
        if msg.get("role") in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current question
    messages.append({"role": "user", "content": body.message})

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-5.5",
            messages=messages,
            max_completion_tokens=1000,
        )

        reply = response.choices[0].message.content.strip()

        return APIResponse(data={
            "reply": reply,
            "tokens_used": response.usage.total_tokens if response.usage else 0,
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


def _build_report_context(report: AnalysisReport) -> str:
    """Build a text summary of the analysis for GPT context."""
    sections = []

    if report.file_inspection:
        fi = json.loads(report.file_inspection)
        sections.append(f"FILE INSPECTION:\n{json.dumps(fi, indent=2)}")

    if report.visual_analysis:
        va = json.loads(report.visual_analysis)
        sections.append(f"VISUAL ANALYSIS:\n{json.dumps(va, indent=2)}")

    if report.geometry_analysis:
        ga = json.loads(report.geometry_analysis)
        sections.append(f"GEOMETRY & ASPECT RATIO:\n{json.dumps(ga, indent=2)}")

    if report.production_analysis:
        pa = json.loads(report.production_analysis)
        sections.append(f"PRODUCTION ANALYSIS (includes Image Quality):\n{json.dumps(pa, indent=2)}")

    if report.product_compatibility:
        pc = json.loads(report.product_compatibility)
        sections.append(f"PRODUCT COMPATIBILITY:\n{json.dumps(pc, indent=2)}")

    if report.risk_assessment:
        ra = json.loads(report.risk_assessment)
        sections.append(f"RISK ASSESSMENT:\n{json.dumps(ra, indent=2)}")

    if report.decision_plan:
        dp = json.loads(report.decision_plan)
        sections.append(f"AI DECISIONS:\n{json.dumps(dp, indent=2)}")

    if report.generation_plan:
        gp = json.loads(report.generation_plan)
        sections.append(f"GENERATION PLAN:\n{json.dumps(gp, indent=2)}")

    sections.append(f"OVERALL SCORE: {report.overall_score}/100")
    sections.append(f"RISK LEVEL: {report.risk_level}")

    return "\n\n".join(sections)
