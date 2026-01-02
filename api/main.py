"""
DataNarrative API
=================
FastAPI application for the DataNarrative platform.

Main entry point that orchestrates:
- Query processing (NLP → Insights → Infogram)
- Data ingestion (Upload → Parse → Store)
- Rendering (Data → Template → Image)
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# === Lifespan Management ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    """
    # Startup
    logger.info("="*50)
    logger.info("DataNarrative API Starting...")
    logger.info("="*50)
    
    # Ensure directories exist
    Path("./storage/uploads").mkdir(parents=True, exist_ok=True)
    Path("./storage/outputs").mkdir(parents=True, exist_ok=True)
    Path("./storage/chroma").mkdir(parents=True, exist_ok=True)
    
    # Initialize components
    try:
        from core.knowledge import get_knowledge_store
        store = get_knowledge_store()
        stats = store.get_stats()
        logger.info(f"Knowledge store initialized: {stats.get('total_chunks', 0)} chunks")
    except Exception as e:
        logger.warning(f"Knowledge store init warning: {e}")
    
    try:
        from core.renderer import get_render_engine
        engine = get_render_engine()
        templates = engine.list_templates()
        logger.info(f"Render engine initialized: {len(templates)} templates available")
    except Exception as e:
        logger.warning(f"Render engine init warning: {e}")
    
    logger.info("API Ready!")
    logger.info("="*50)
    
    yield
    
    # Shutdown
    logger.info("DataNarrative API Shutting down...")


# === Create Application ===

app = FastAPI(
    title="DataNarrative API",
    description="""
    Intelligence-driven visual storytelling platform.
    
    Transform raw data into compelling infographics through AI-powered analysis.
    
    ## Features
    
    - **Query Mode**: Ask questions, get infographics
    - **Upload Mode**: Upload data, build knowledge base
    - **Render Mode**: Create infographics directly
    
    ## Output Modes
    
    - **Data Mode**: Single infographic with key insights
    - **Story Mode**: 5-frame narrative (Context → Change → Evidence → Consequence → Implication)
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# === Middleware ===

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Static Files ===

# Serve generated outputs
app.mount(
    "/static/outputs",
    StaticFiles(directory="./storage/outputs"),
    name="outputs"
)


# === Error Handlers ===

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if app.debug else None
        }
    )


# === Import and Include Routes ===

from api.routes import query, ingest, render

app.include_router(query.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(render.router, prefix="/api/v1")


# === Root Endpoints ===

@app.get("/", tags=["Root"])
async def root():
    """
    Welcome endpoint.
    """
    return {
        "name": "DataNarrative API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "query": "/api/v1/query",
            "ingest": "/api/v1/ingest",
            "render": "/api/v1/render"
        }
    }


@app.get("/health", tags=["Root"])
async def health_check():
    """
    Health check endpoint.
    """
    health = {
        "status": "healthy",
        "components": {}
    }
    
    # Check knowledge store
    try:
        from core.knowledge import get_knowledge_store
        store = get_knowledge_store()
        stats = store.get_stats()
        health["components"]["knowledge_store"] = {
            "status": "ok",
            "chunks": stats.get("total_chunks", 0)
        }
    except Exception as e:
        health["components"]["knowledge_store"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check renderer
    try:
        from core.renderer import get_render_engine
        engine = get_render_engine()
        templates = engine.list_templates()
        health["components"]["renderer"] = {
            "status": "ok",
            "templates": len(templates)
        }
    except Exception as e:
        health["components"]["renderer"] = {
            "status": "error",
            "error": str(e)
        }
    
    return health


@app.get("/api/v1/config", tags=["Root"])
async def get_config():
    """
    Get public configuration.
    """
    try:
        from config import DOMAIN_CONFIG, OUTPUT_MODES, INSIGHT_TYPES
        
        return {
            "domains": list(DOMAIN_CONFIG.keys()),
            "output_modes": OUTPUT_MODES,
            "insight_types": INSIGHT_TYPES,
            "supported_formats": [".csv", ".xlsx", ".xls"],
            "max_file_size_mb": 10,
            "templates": [
                "hero_stat",
                "trend_line",
                "ranking_bar",
                "versus",
                "story_five_frame",
                "story_carousel"
            ]
        }
    except Exception as e:
        return {
            "domains": ["education", "health", "economy", "agriculture"],
            "output_modes": ["story", "data"],
            "templates": ["hero_stat", "trend_line", "ranking_bar", "versus"]
        }


# === Run Configuration ===

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
