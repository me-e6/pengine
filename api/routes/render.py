"""
Render Routes
=============
Endpoints for direct infographic rendering.
Use when you want to create infographics without going through the query pipeline.
"""

import logging
from typing import Optional, List, Any
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/render", tags=["Render"])


# === Request/Response Models ===

class MetricInput(BaseModel):
    """A metric to display"""
    value: Any = Field(..., description="The metric value")
    label: str = Field(..., description="Label for the metric")
    change: Optional[float] = Field(None, description="Percentage change")
    unit: Optional[str] = Field("", description="Unit suffix (%, pts, etc.)")


class ChartDataInput(BaseModel):
    """A data point for charts"""
    label: str = Field(..., description="Category or x-axis label")
    value: float = Field(..., description="The value")
    period: Optional[Any] = Field(None, description="Time period (for line charts)")


class NarrativeFrameInput(BaseModel):
    """A story frame"""
    type: str = Field(..., description="Frame type: context, change, evidence, consequence, implication")
    headline: str = Field(..., description="Frame headline")
    body_text: str = Field(..., description="Frame body text")
    key_metric: Optional[str] = Field(None, description="Key metric to display")
    key_metric_label: Optional[str] = Field(None, description="Label for key metric")


class RenderRequest(BaseModel):
    """Request to render an infographic"""
    template: str = Field("hero_stat", description="Template to use")
    output_mode: str = Field("data", description="'story' or 'data' mode")
    story_format: str = Field("single", description="'single' or 'carousel' for story mode")
    
    # Content
    title: str = Field(..., description="Main title")
    subtitle: Optional[str] = Field(None, description="Subtitle")
    
    # Data
    metrics: Optional[List[MetricInput]] = Field(None, description="Metrics to display")
    chart_data: Optional[List[ChartDataInput]] = Field(None, description="Chart data points")
    insights: Optional[List[str]] = Field(None, description="Insight text bullets")
    narrative_frames: Optional[List[NarrativeFrameInput]] = Field(None, description="Story frames")
    
    # Styling
    domain: str = Field("general", description="Domain for color scheme")
    sentiment: str = Field("neutral", description="Sentiment for colors")
    
    # Attribution
    source: Optional[str] = Field(None, description="Data source attribution")
    time_period: Optional[str] = Field(None, description="Time period covered")
    
    # Options
    show_branding: bool = Field(True, description="Show DataNarrative branding")
    
    class Config:
        json_schema_extra = {
            "example": {
                "template": "hero_stat",
                "title": "Telangana Literacy Rate",
                "subtitle": "2023 Census Data",
                "metrics": [
                    {"value": 89.5, "label": "Literacy Rate", "change": 7.6, "unit": "%"}
                ],
                "insights": [
                    "Highest rate in state history",
                    "Urban areas lead with 92.8%"
                ],
                "domain": "education",
                "sentiment": "positive",
                "source": "Census 2023"
            }
        }


class RenderResponse(BaseModel):
    """Response after rendering"""
    success: bool
    infogram_id: str
    image_url: str
    template_used: str
    width: int
    height: int
    render_time_ms: float
    
    # For carousel
    image_urls: Optional[List[str]] = None
    image_count: int = 1


class TemplateInfo(BaseModel):
    """Information about a template"""
    id: str
    name: str
    description: str
    best_for: List[str]


class InfogramStatus(BaseModel):
    """Status of an infogram"""
    id: str
    status: str  # pending, approved, rejected
    created_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None


# === Global State ===
_infograms: dict = {}


# === Endpoints ===

@router.post("/manual", response_model=RenderResponse)
async def render_manual(request: RenderRequest):
    """
    Manually render an infographic with provided data.
    
    Use this endpoint when you:
    - Have your own data to visualize
    - Want to create a specific type of infographic
    - Don't need AI analysis
    
    Returns the generated image URL.
    """
    import time
    start_time = time.time()
    
    try:
        from core.renderer import RenderEngine, RenderSpec
        
        # Build RenderSpec
        spec = RenderSpec(
            output_mode=request.output_mode,
            template_type=request.template,
            story_format=request.story_format,
            title=request.title,
            subtitle=request.subtitle or "",
            metrics=[m.model_dump() for m in request.metrics] if request.metrics else [],
            chart_data=[c.model_dump() for c in request.chart_data] if request.chart_data else [],
            insights=request.insights or [],
            narrative_frames=[f.model_dump() for f in request.narrative_frames] if request.narrative_frames else [],
            domain=request.domain,
            sentiment=request.sentiment,
            source=request.source or "",
            time_period=request.time_period or "",
            show_branding=request.show_branding
        )
        
        # Render
        engine = RenderEngine(output_dir="./storage/outputs")
        result = engine.render(spec)
        
        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Render failed: {result.error_message}"
            )
        
        # Save and generate URLs
        infogram_id = str(uuid.uuid4())[:8]
        image_urls = []
        
        if request.story_format == "carousel" and result.images:
            # Save carousel images
            paths = engine.save_carousel(result, prefix=f"infogram_{infogram_id}")
            for i, path in enumerate(paths):
                filename = path.split('/')[-1]
                image_urls.append(f"/static/outputs/{filename}")
        else:
            # Save single image
            filename = f"infogram_{infogram_id}.png"
            engine.save(result, filename)
            image_urls.append(f"/static/outputs/{filename}")
        
        # Store metadata
        _infograms[infogram_id] = {
            "id": infogram_id,
            "template": request.template,
            "title": request.title,
            "status": "pending",
            "created_at": datetime.now(),
            "image_urls": image_urls,
            "approved_at": None,
            "approved_by": None
        }
        
        render_time = (time.time() - start_time) * 1000
        
        return RenderResponse(
            success=True,
            infogram_id=infogram_id,
            image_url=image_urls[0],
            image_urls=image_urls if len(image_urls) > 1 else None,
            image_count=len(image_urls),
            template_used=result.template_used,
            width=result.width,
            height=result.height,
            render_time_ms=render_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Render failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=List[TemplateInfo])
async def list_templates():
    """
    List all available infographic templates.
    
    Each template is designed for specific types of data visualization.
    """
    try:
        from core.renderer import RenderEngine
        
        engine = RenderEngine()
        templates = engine.list_templates()
        
        return [
            TemplateInfo(
                id=t["id"],
                name=t.get("name", t["id"]),
                description=t.get("description", ""),
                best_for=t.get("best_for", [])
            )
            for t in templates
        ]
        
    except Exception as e:
        logger.error(f"List templates failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/infogram/{infogram_id}")
async def get_infogram(infogram_id: str):
    """
    Get details of a specific infogram.
    """
    if infogram_id not in _infograms:
        raise HTTPException(status_code=404, detail="Infogram not found")
    
    return _infograms[infogram_id]


@router.get("/infogram/{infogram_id}/image")
async def get_infogram_image(infogram_id: str, index: int = Query(0, ge=0)):
    """
    Get the image file for an infogram.
    
    For carousel infograms, use index parameter (0-4).
    """
    if infogram_id not in _infograms:
        raise HTTPException(status_code=404, detail="Infogram not found")
    
    infogram = _infograms[infogram_id]
    image_urls = infogram.get("image_urls", [])
    
    if index >= len(image_urls):
        raise HTTPException(status_code=404, detail=f"Image index {index} not found")
    
    # Extract filename from URL
    filename = image_urls[index].split('/')[-1]
    filepath = f"./storage/outputs/{filename}"
    
    try:
        return FileResponse(
            filepath,
            media_type="image/png",
            filename=filename
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Image file not found")


@router.patch("/infogram/{infogram_id}/status")
async def update_infogram_status(
    infogram_id: str,
    status: str = Query(..., description="New status: approved or rejected"),
    approved_by: Optional[str] = Query(None, description="Approver name")
):
    """
    Update the approval status of an infogram.
    
    Used in the editorial workflow before publishing.
    """
    if infogram_id not in _infograms:
        raise HTTPException(status_code=404, detail="Infogram not found")
    
    if status not in ["approved", "rejected", "pending"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    _infograms[infogram_id]["status"] = status
    
    if status == "approved":
        _infograms[infogram_id]["approved_at"] = datetime.now()
        _infograms[infogram_id]["approved_by"] = approved_by
    
    return {
        "success": True,
        "infogram_id": infogram_id,
        "new_status": status
    }


@router.get("/queue")
async def get_approval_queue(
    status: str = Query("pending", description="Filter by status"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get the approval queue for infograms.
    
    Returns infograms waiting for editorial review.
    """
    infograms = [
        i for i in _infograms.values()
        if i.get("status") == status
    ]
    
    # Sort by created_at descending
    infograms.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    
    return {
        "total": len(infograms),
        "status": status,
        "items": infograms[:limit]
    }


@router.get("/gallery")
async def get_gallery(
    limit: int = Query(20, ge=1, le=100),
    domain: Optional[str] = Query(None, description="Filter by domain")
):
    """
    Get the gallery of approved/published infograms.
    """
    infograms = [
        i for i in _infograms.values()
        if i.get("status") == "approved"
    ]
    
    # Sort by approved_at descending
    infograms.sort(key=lambda x: x.get("approved_at") or datetime.min, reverse=True)
    
    return {
        "total": len(infograms),
        "items": infograms[:limit]
    }


@router.post("/quick")
async def quick_render(
    title: str = Query(..., description="Title"),
    value: float = Query(..., description="Main value"),
    label: str = Query(..., description="Value label"),
    change: Optional[float] = Query(None, description="Percentage change"),
    domain: str = Query("general", description="Domain"),
    template: str = Query("hero_stat", description="Template")
):
    """
    Quick render endpoint for simple single-metric infographics.
    
    Perfect for quick one-off visualizations.
    """
    request = RenderRequest(
        template=template,
        title=title,
        metrics=[MetricInput(value=value, label=label, change=change)],
        domain=domain
    )
    
    return await render_manual(request)
