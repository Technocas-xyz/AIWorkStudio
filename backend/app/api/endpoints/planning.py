"""Production Planning Workspace API."""

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
from app.models.reconstruction import ProductProfile, ProductionPlan

router = APIRouter()

# Default product profiles
DEFAULT_PRODUCTS = [
    {"name": "dtf_transfer", "display_name": "DTF Transfer", "category": "transfer", "max_width": 20, "max_height": 28, "requires_transparency": True, "requires_bleed": False},
    {"name": "tshirt_adult", "display_name": "T-Shirt (Adult)", "category": "apparel", "max_width": 14, "max_height": 18, "requires_transparency": True, "requires_bleed": False},
    {"name": "tshirt_youth", "display_name": "T-Shirt (Youth)", "category": "apparel", "max_width": 10, "max_height": 14, "requires_transparency": True, "requires_bleed": False},
    {"name": "hoodie", "display_name": "Hoodie", "category": "apparel", "max_width": 14, "max_height": 16, "requires_transparency": True, "requires_bleed": False},
    {"name": "gangsheet", "display_name": "Gangsheet", "category": "transfer", "max_width": 22, "max_height": 72, "requires_transparency": True, "requires_bleed": False},
    {"name": "sticker", "display_name": "Sticker", "category": "print", "max_width": 6, "max_height": 6, "requires_transparency": True, "requires_bleed": True, "bleed_size": 0.0625},
    {"name": "poster", "display_name": "Poster", "category": "print", "max_width": 24, "max_height": 36, "requires_transparency": False, "requires_bleed": True, "bleed_size": 0.125},
    {"name": "mug", "display_name": "Mug", "category": "accessory", "max_width": 9.5, "max_height": 3.5, "requires_transparency": False, "requires_bleed": False},
    {"name": "embroidery", "display_name": "Embroidery", "category": "apparel", "max_width": 12, "max_height": 12, "requires_transparency": True, "requires_bleed": False},
    {"name": "cap", "display_name": "Cap", "category": "accessory", "max_width": 4.5, "max_height": 2.5, "requires_transparency": True, "requires_bleed": False},
    {"name": "sublimation", "display_name": "Sublimation", "category": "print", "max_width": 16, "max_height": 20, "requires_transparency": False, "requires_bleed": True, "bleed_size": 0.25},
    {"name": "uv_print", "display_name": "UV Print", "category": "print", "max_width": 12, "max_height": 12, "requires_transparency": True, "requires_bleed": False},
]


@router.get("/products", response_model=APIResponse)
async def get_products(current_user: User = Depends(get_current_user)):
    """Get all available product profiles."""
    return APIResponse(data=DEFAULT_PRODUCTS)


@router.post("/create", response_model=APIResponse)
async def create_production_plan(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a production plan for a specific product."""
    artwork_id = body.get("artwork_id")
    product_name = body.get("product")
    if not artwork_id or not product_name:
        raise HTTPException(status_code=400, detail="artwork_id and product required")

    # Load artwork
    art_result = await db.execute(select(Artwork).where(Artwork.id == artwork_id, Artwork.is_deleted == False))
    artwork = art_result.scalar_one_or_none()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    # Find product profile
    product = next((p for p in DEFAULT_PRODUCTS if p["name"] == product_name), None)
    if not product:
        raise HTTPException(status_code=400, detail="Unknown product")

    # Calculate sizing
    dpi = artwork.resolution_dpi or 72
    art_width_in = (artwork.width or 0) / max(dpi, 1)
    art_height_in = (artwork.height or 0) / max(dpi, 1)

    # Fit within product max area
    scale_w = product["max_width"] / art_width_in if art_width_in > 0 else 1
    scale_h = product["max_height"] / art_height_in if art_height_in > 0 else 1
    scale = min(scale_w, scale_h, 1.0)  # Don't upscale beyond original

    print_width = round(art_width_in * scale, 2)
    print_height = round(art_height_in * scale, 2)

    # Determine orientation
    orientation = "landscape" if print_width > print_height else "portrait" if print_height > print_width else "square"
    aspect_ratio = f"{round(print_width)}:{round(print_height)}" if print_width > 0 else "1:1"

    # Validate and generate warnings
    warnings = _validate_plan(artwork, product, print_width, print_height, dpi)

    # Specifications
    specs = {
        "source_dimensions": f"{artwork.width}Ã—{artwork.height}px",
        "source_dpi": dpi,
        "target_dpi": 300,
        "print_area": f"{print_width}\" Ã— {print_height}\"",
        "max_product_area": f"{product['max_width']}\" Ã— {product['max_height']}\"",
        "color_profile": "sRGB",
        "output_format": "PNG",
        "transparent_bg": product["requires_transparency"],
        "bleed": f"{product.get('bleed_size', 0)}\"" if product.get("requires_bleed") else "None",
        "scale_factor": round(scale, 3),
    }

    plan = ProductionPlan(
        id=str(uuid.uuid4()),
        artwork_id=artwork_id,
        product_name=product_name,
        status="draft",
        print_width=print_width,
        print_height=print_height,
        target_dpi=300,
        aspect_ratio=aspect_ratio,
        orientation=orientation,
        placement=body.get("placement", "center"),
        scale_factor=scale,
        requires_bleed=product.get("requires_bleed", False),
        output_format="PNG",
        color_profile="sRGB",
        warnings=json.dumps(warnings),
        specifications=json.dumps(specs),
        created_by_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(plan)
    await db.flush()

    return APIResponse(message="Production plan created", data={
        "id": plan.id,
        "product": product_name,
        "product_display": product["display_name"],
        "print_width": print_width,
        "print_height": print_height,
        "orientation": orientation,
        "aspect_ratio": aspect_ratio,
        "scale_factor": round(scale, 3),
        "specifications": specs,
        "warnings": warnings,
        "status": plan.status,
    })


@router.get("/{plan_id}", response_model=APIResponse)
async def get_production_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ProductionPlan).where(ProductionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return APIResponse(data={
        "id": plan.id,
        "artwork_id": plan.artwork_id,
        "product": plan.product_name,
        "print_width": plan.print_width,
        "print_height": plan.print_height,
        "aspect_ratio": plan.aspect_ratio,
        "orientation": plan.orientation,
        "placement": plan.placement,
        "scale_factor": plan.scale_factor,
        "target_dpi": plan.target_dpi,
        "status": plan.status,
        "specifications": json.loads(plan.specifications) if plan.specifications else {},
        "warnings": json.loads(plan.warnings) if plan.warnings else [],
    })


@router.post("/validate", response_model=APIResponse)
async def validate_production_plan(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan_id = body.get("plan_id")
    result = await db.execute(select(ProductionPlan).where(ProductionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    warnings = json.loads(plan.warnings) if plan.warnings else []
    errors = [w for w in warnings if w.get("severity") == "critical"]

    valid = len(errors) == 0
    if valid:
        plan.status = "validated"
        await db.flush()

    return APIResponse(data={"valid": valid, "errors": errors, "warnings": warnings})


@router.post("/approve", response_model=APIResponse)
async def approve_production_plan(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan_id = body.get("plan_id")
    result = await db.execute(select(ProductionPlan).where(ProductionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.status = "approved"
    await db.flush()
    return APIResponse(message="Production plan approved")


@router.get("/artwork/{artwork_id}/latest", response_model=APIResponse)
async def get_latest_production_plan(
    artwork_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest production plan for an artwork."""
    result = await db.execute(
        select(ProductionPlan)
        .where(ProductionPlan.artwork_id == artwork_id, ProductionPlan.is_deleted == False)
        .order_by(ProductionPlan.created_at.desc())
    )
    plan = result.scalars().first()
    if not plan:
        return APIResponse(data=None, message="No production plan found")

    return APIResponse(data={
        "id": plan.id,
        "artwork_id": plan.artwork_id,
        "product": plan.product_name,
        "product_display": plan.product_name.replace("_", " ").title(),
        "print_width": plan.print_width,
        "print_height": plan.print_height,
        "aspect_ratio": plan.aspect_ratio,
        "orientation": plan.orientation,
        "placement": plan.placement,
        "scale_factor": plan.scale_factor,
        "target_dpi": plan.target_dpi,
        "status": plan.status,
        "specifications": json.loads(plan.specifications) if plan.specifications else {},
        "warnings": json.loads(plan.warnings) if plan.warnings else [],
    })


def _validate_plan(artwork, product: dict, print_w: float, print_h: float, dpi: int) -> list:
    warnings = []

    # DPI check
    effective_dpi = (artwork.width or 0) / print_w if print_w > 0 else 0
    if effective_dpi < 200:
        warnings.append({"severity": "critical", "message": f"Effective DPI ({effective_dpi:.0f}) below minimum 200 for {product['display_name']}"})
    elif effective_dpi < 300:
        warnings.append({"severity": "medium", "message": f"Effective DPI ({effective_dpi:.0f}) below recommended 300"})

    # Transparency
    if product["requires_transparency"] and not artwork.has_alpha_channel:
        warnings.append({"severity": "high", "message": "Product requires transparent background but artwork has none"})

    # Size
    if print_w > product["max_width"] or print_h > product["max_height"]:
        warnings.append({"severity": "high", "message": f"Print size exceeds product maximum ({product['max_width']}\"Ã—{product['max_height']}\")"})

    # Small size
    if print_w < 2 and print_h < 2:
        warnings.append({"severity": "medium", "message": "Very small print size - may lack visible detail"})

    return warnings
