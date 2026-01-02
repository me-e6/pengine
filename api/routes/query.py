"""
Query Routes
============
Endpoints for natural language queries.
The main entry point for users asking questions about data.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["Query"])


# === Request/Response Models ===

class QueryRequest(BaseModel):
    """Request to process a natural language query"""
    query: str = Field(..., description="Natural language question", min_length=3, max_length=500)
    domain_hint: Optional[str] = Field(None, description="Hint about domain (education, health, etc.)")
    force_mode: Optional[str] = Field(None, description="Force 'story' or 'data' mode")
    include_image: bool = Field(True, description="Generate infographic image")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "How has literacy changed in Telangana from 2015 to 2023?",
                "domain_hint": "education",
                "force_mode": None,
                "include_image": True
            }
        }


class QueryAnalysisResponse(BaseModel):
    """Analysis of the query"""
    intent: str
    intent_confidence: float
    topics: List[str]
    locations: List[str]
    time_references: List[str]
    domain_hint: Optional[str]
    requires_historical: bool
    preferred_output: str


class InsightResponse(BaseModel):
    """A detected insight"""
    type: str
    summary: str
    confidence: float
    metric_name: Optional[str] = None
    current_value: Optional[float] = None
    change_percentage: Optional[float] = None
    direction: Optional[str] = None
    sentiment: Optional[str] = None


class NarrativeFrameResponse(BaseModel):
    """A single story frame"""
    type: str
    headline: str
    body_text: str
    key_metric: Optional[str] = None
    key_metric_label: Optional[str] = None


class QueryResponse(BaseModel):
    """Complete response to a query"""
    success: bool
    query: str
    
    # Analysis
    analysis: QueryAnalysisResponse
    
    # Results
    output_mode: str
    template_used: str
    
    # Insights
    insights: List[InsightResponse]
    primary_insight: Optional[InsightResponse] = None
    
    # Narrative (for story mode)
    narrative_title: Optional[str] = None
    narrative_subtitle: Optional[str] = None
    narrative_frames: Optional[List[NarrativeFrameResponse]] = None
    
    # Image
    image_url: Optional[str] = None
    image_id: Optional[str] = None
    
    # Metadata
    sources_used: List[str]
    confidence: float
    processing_time_ms: float
    
    # For debugging
    reasoning_notes: Optional[List[str]] = None


class SuggestionResponse(BaseModel):
    """Suggested queries"""
    suggestions: List[str]
    domain: Optional[str] = None


class QueryHistoryItem(BaseModel):
    """A query history item"""
    id: str
    query: str
    timestamp: datetime
    output_mode: str
    template: str
    image_id: Optional[str] = None
    status: str  # pending, approved, rejected


# === Global State (would be database in production) ===
_query_history: List[dict] = []
_generated_images: dict = {}


# === Endpoints ===

@router.post("", response_model=QueryResponse)
async def process_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Process a natural language query and generate an infographic.
    
    This is the main endpoint that:
    1. Analyzes the query to understand intent
    2. Retrieves relevant data from knowledge base
    3. Detects insights from the data
    4. Generates narrative (if story mode)
    5. Renders infographic image
    
    Returns complete analysis, insights, and image URL.
    """
    import time
    import uuid
    start_time = time.time()
    
    try:
        # Import modules
        from core.intelligence import ReasoningEngine, QueryAnalyzer
        from core.knowledge import get_knowledge_store
        from core.renderer import get_render_engine, RenderSpec
        
        logger.info(f"Processing query: {request.query}")
        
        # Step 1: Initialize components
        knowledge_store = get_knowledge_store()
        reasoning_engine = ReasoningEngine(knowledge_store=knowledge_store)
        render_engine = get_render_engine()
        
        # Step 2: Run reasoning pipeline
        reasoning_result = await reasoning_engine.reason(
            query=request.query,
            force_mode=request.force_mode,
            domain_override=request.domain_hint
        )
        
        # Step 3: Build analysis response
        analysis = QueryAnalysisResponse(
            intent=reasoning_result.query_analysis.intent.value,
            intent_confidence=reasoning_result.query_analysis.intent_confidence,
            topics=reasoning_result.query_analysis.topics,
            locations=reasoning_result.query_analysis.locations,
            time_references=reasoning_result.query_analysis.time_references,
            domain_hint=reasoning_result.query_analysis.domain_hint,
            requires_historical=reasoning_result.query_analysis.requires_historical,
            preferred_output=reasoning_result.query_analysis.preferred_output
        )
        
        # Step 4: Build insights response
        insights = []
        for insight in reasoning_result.insights:
            insights.append(InsightResponse(
                type=insight.insight_type.value,
                summary=insight.summary,
                confidence=insight.confidence,
                metric_name=insight.metric_name,
                current_value=insight.current_value if isinstance(insight.current_value, (int, float)) else None,
                change_percentage=insight.change_percentage,
                direction=insight.direction,
                sentiment=insight.sentiment.value if hasattr(insight.sentiment, 'value') else str(insight.sentiment)
            ))
        
        primary_insight = None
        if reasoning_result.primary_insight:
            pi = reasoning_result.primary_insight
            primary_insight = InsightResponse(
                type=pi.insight_type.value,
                summary=pi.summary,
                confidence=pi.confidence,
                metric_name=pi.metric_name,
                current_value=pi.current_value if isinstance(pi.current_value, (int, float)) else None,
                change_percentage=pi.change_percentage,
                direction=pi.direction,
                sentiment=pi.sentiment.value if hasattr(pi.sentiment, 'value') else str(pi.sentiment)
            )
        
        # Step 5: Build narrative response (if story mode)
        narrative_title = None
        narrative_subtitle = None
        narrative_frames = None
        
        if reasoning_result.narrative:
            narrative_title = reasoning_result.narrative.title
            narrative_subtitle = reasoning_result.narrative.subtitle
            narrative_frames = [
                NarrativeFrameResponse(
                    type=f.frame_type,
                    headline=f.headline,
                    body_text=f.body_text,
                    key_metric=f.key_metric,
                    key_metric_label=f.key_metric_label
                )
                for f in reasoning_result.narrative.get_frames()
            ]
        
        # Step 6: Render image
        image_url = None
        image_id = None
        
        if request.include_image:
            render_output = render_engine.render_from_reasoning(reasoning_result)
            
            if render_output.success:
                image_id = str(uuid.uuid4())[:8]
                filename = f"query_{image_id}.png"
                path = render_engine.save(render_output, filename)
                
                if path:
                    image_url = f"/static/outputs/{filename}"
                    _generated_images[image_id] = {
                        "path": path,
                        "query": request.query,
                        "created_at": datetime.now()
                    }
        
        # Step 7: Save to history
        history_id = str(uuid.uuid4())[:8]
        _query_history.append({
            "id": history_id,
            "query": request.query,
            "timestamp": datetime.now(),
            "output_mode": reasoning_result.output_mode,
            "template": reasoning_result.recommended_template,
            "image_id": image_id,
            "status": "pending"
        })
        
        processing_time = (time.time() - start_time) * 1000
        
        return QueryResponse(
            success=True,
            query=request.query,
            analysis=analysis,
            output_mode=reasoning_result.output_mode,
            template_used=reasoning_result.recommended_template,
            insights=insights,
            primary_insight=primary_insight,
            narrative_title=narrative_title,
            narrative_subtitle=narrative_subtitle,
            narrative_frames=narrative_frames,
            image_url=image_url,
            image_id=image_id,
            sources_used=reasoning_result.sources_used,
            confidence=reasoning_result.overall_confidence,
            processing_time_ms=processing_time,
            reasoning_notes=reasoning_result.reasoning_notes
        )
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze")
async def analyze_query(q: str = Query(..., description="Query to analyze")):
    """
    Analyze a query without generating results.
    
    Useful for understanding what the system understood from the query.
    """
    try:
        from core.intelligence import QueryAnalyzer
        
        analyzer = QueryAnalyzer()
        result = analyzer.analyze(q)
        
        return {
            "query": q,
            "normalized": result.normalized_query,
            "intent": result.intent.value,
            "intent_confidence": result.intent_confidence,
            "topics": result.topics,
            "locations": result.locations,
            "time_references": result.time_references,
            "domain_hint": result.domain_hint,
            "requires_historical": result.requires_historical,
            "requires_comparison": result.requires_comparison,
            "preferred_output": result.preferred_output,
            "search_keywords": result.search_keywords
        }
        
    except Exception as e:
        logger.error(f"Query analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions", response_model=SuggestionResponse)
async def get_suggestions(domain: Optional[str] = None):
    """
    Get suggested queries based on available data.
    
    Returns example queries that users can try.
    """
    # Static suggestions for now - would be dynamic based on knowledge base
    suggestions_by_domain = {
        "education": [
            "How has literacy changed in Telangana from 2015 to 2023?",
            "Which district has the highest literacy rate?",
            "Compare urban vs rural literacy in Telangana",
            "Show enrollment trends over the last 5 years",
            "What is the current teacher-student ratio?"
        ],
        "health": [
            "What is the current vaccination rate?",
            "How has infant mortality changed over time?",
            "Compare hospital beds across districts",
            "Show disease prevalence trends",
            "Which district has the best healthcare access?"
        ],
        "economy": [
            "What is Telangana's current GDP growth?",
            "How has employment changed since 2015?",
            "Compare income levels across districts",
            "Show tax revenue trends",
            "Which sector contributes most to GDP?"
        ],
        "agriculture": [
            "What are the current crop yields?",
            "How has irrigation coverage changed?",
            "Compare MSP trends for major crops",
            "Show rainfall patterns over the years",
            "Which district has the highest agricultural output?"
        ]
    }
    
    if domain and domain in suggestions_by_domain:
        return SuggestionResponse(
            suggestions=suggestions_by_domain[domain],
            domain=domain
        )
    
    # Return mixed suggestions
    all_suggestions = []
    for suggestions in suggestions_by_domain.values():
        all_suggestions.extend(suggestions[:2])
    
    return SuggestionResponse(suggestions=all_suggestions[:8])


@router.get("/history")
async def get_query_history(
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    Get query history for approval workflow.
    """
    history = _query_history.copy()
    
    if status:
        history = [h for h in history if h.get("status") == status]
    
    # Sort by timestamp descending
    history.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
    
    return {
        "total": len(history),
        "items": history[:limit]
    }


@router.get("/history/{query_id}")
async def get_query_detail(query_id: str):
    """
    Get details of a specific query.
    """
    for item in _query_history:
        if item.get("id") == query_id:
            return item
    
    raise HTTPException(status_code=404, detail="Query not found")
