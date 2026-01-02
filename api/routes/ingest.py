"""
Ingest Routes
=============
Endpoints for data ingestion and management.
Upload CSV/Excel files to build the knowledge base.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["Ingest"])


# === Request/Response Models ===

class ManualDataRequest(BaseModel):
    """Request to manually input data"""
    source_name: str = Field(..., description="Name for this data source")
    domain: Optional[str] = Field(None, description="Domain (education, health, etc.)")
    data: List[dict] = Field(..., description="List of data records")
    columns: Optional[List[str]] = Field(None, description="Column definitions")
    description: Optional[str] = Field(None, description="Description of the data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_name": "Literacy Survey 2023",
                "domain": "education",
                "data": [
                    {"district": "Hyderabad", "literacy_rate": 89.5, "year": 2023},
                    {"district": "Warangal", "literacy_rate": 86.5, "year": 2023}
                ],
                "description": "District-wise literacy rates from latest survey"
            }
        }


class IngestResultResponse(BaseModel):
    """Response after ingestion"""
    success: bool
    file_id: str
    filename: str
    source_name: str
    
    tables_found: int
    chunks_created: int
    chunks_stored: int
    
    domains_detected: List[str]
    has_historical_data: bool
    time_range: Optional[List] = None
    regions_detected: List[str]
    
    processing_time_seconds: float
    errors: List[str]
    warnings: List[str]


class DataSourceResponse(BaseModel):
    """Information about a data source"""
    id: str
    name: str
    filename: str
    domain: str
    chunks: int
    uploaded_at: datetime
    status: str


class KnowledgeStatsResponse(BaseModel):
    """Knowledge base statistics"""
    total_chunks: int
    total_sources: int
    domains: dict
    regions: List[str]
    storage_path: str


# === Global State ===
_data_sources: dict = {}


# === Endpoints ===

@router.post("/upload", response_model=IngestResultResponse)
async def upload_file(
    file: UploadFile = File(..., description="CSV or Excel file to upload"),
    source_name: str = Form(..., description="Name for this data source"),
    domain_hint: Optional[str] = Form(None, description="Optional domain hint"),
    description: Optional[str] = Form(None, description="Optional description")
):
    """
    Upload a CSV or Excel file to the knowledge base.
    
    The file will be:
    1. Parsed to extract tables
    2. Chunked into semantic units
    3. Tagged with domain and entities
    4. Stored in the vector database
    
    Supports: .csv, .xlsx, .xls
    """
    import time
    start_time = time.time()
    
    # Validate file type
    allowed_extensions = ['.csv', '.xlsx', '.xls']
    file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}"
        )
    
    try:
        from core.ingest import IngestPipeline
        from core.knowledge import get_knowledge_store
        
        # Read file content
        content = await file.read()
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Initialize pipeline with knowledge store
        knowledge_store = get_knowledge_store()
        pipeline = IngestPipeline(
            knowledge_store=knowledge_store,
            uploads_dir="./storage/uploads"
        )
        
        # Run ingestion
        result = await pipeline.ingest_from_upload(
            file_content=content,
            filename=file.filename,
            source_name=source_name,
            domain_hint=domain_hint
        )
        
        # Store source metadata
        if result.success:
            _data_sources[result.file_id] = {
                "id": result.file_id,
                "name": source_name,
                "filename": result.filename,
                "domain": result.domains_detected[0] if result.domains_detected else "other",
                "chunks": result.chunks_stored,
                "uploaded_at": datetime.now(),
                "status": "active",
                "description": description
            }
        
        processing_time = time.time() - start_time
        
        return IngestResultResponse(
            success=result.success,
            file_id=result.file_id,
            filename=result.filename,
            source_name=source_name,
            tables_found=result.tables_found,
            chunks_created=result.chunks_created,
            chunks_stored=result.chunks_stored,
            domains_detected=result.domains_detected,
            has_historical_data=result.has_historical_data,
            time_range=list(result.time_range) if result.time_range else None,
            regions_detected=result.regions_detected,
            processing_time_seconds=processing_time,
            errors=result.errors,
            warnings=result.warnings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manual", response_model=IngestResultResponse)
async def ingest_manual_data(request: ManualDataRequest):
    """
    Manually input data as JSON.
    
    Useful for:
    - Small datasets
    - API integrations
    - Testing
    
    Data will be processed and stored in the knowledge base.
    """
    import time
    import json
    import tempfile
    import os
    
    start_time = time.time()
    
    try:
        from core.ingest import IngestPipeline
        from core.knowledge import get_knowledge_store
        
        if not request.data:
            raise HTTPException(status_code=400, detail="No data provided")
        
        # Convert to CSV and process
        import csv
        import io
        
        # Get columns from first record or provided columns
        if request.columns:
            columns = request.columns
        elif request.data:
            columns = list(request.data[0].keys())
        else:
            raise HTTPException(status_code=400, detail="Cannot determine columns")
        
        # Write to CSV string
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(request.data)
        csv_content = output.getvalue().encode('utf-8')
        
        # Initialize pipeline
        knowledge_store = get_knowledge_store()
        pipeline = IngestPipeline(
            knowledge_store=knowledge_store,
            uploads_dir="./storage/uploads"
        )
        
        # Process
        file_id = str(uuid.uuid4())[:8]
        filename = f"manual_{file_id}.csv"
        
        result = await pipeline.ingest_from_upload(
            file_content=csv_content,
            filename=filename,
            source_name=request.source_name,
            domain_hint=request.domain
        )
        
        # Store source metadata
        if result.success:
            _data_sources[result.file_id] = {
                "id": result.file_id,
                "name": request.source_name,
                "filename": filename,
                "domain": result.domains_detected[0] if result.domains_detected else "other",
                "chunks": result.chunks_stored,
                "uploaded_at": datetime.now(),
                "status": "active",
                "description": request.description
            }
        
        processing_time = time.time() - start_time
        
        return IngestResultResponse(
            success=result.success,
            file_id=result.file_id,
            filename=filename,
            source_name=request.source_name,
            tables_found=result.tables_found,
            chunks_created=result.chunks_created,
            chunks_stored=result.chunks_stored,
            domains_detected=result.domains_detected,
            has_historical_data=result.has_historical_data,
            time_range=list(result.time_range) if result.time_range else None,
            regions_detected=result.regions_detected,
            processing_time_seconds=processing_time,
            errors=result.errors,
            warnings=result.warnings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual ingest failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources")
async def list_sources(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    List all data sources in the knowledge base.
    """
    sources = list(_data_sources.values())
    
    if domain:
        sources = [s for s in sources if s.get("domain") == domain]
    
    if status:
        sources = [s for s in sources if s.get("status") == status]
    
    # Sort by upload date
    sources.sort(key=lambda x: x.get("uploaded_at", datetime.min), reverse=True)
    
    return {
        "total": len(sources),
        "sources": sources
    }


@router.get("/sources/{source_id}", response_model=DataSourceResponse)
async def get_source(source_id: str):
    """
    Get details of a specific data source.
    """
    if source_id not in _data_sources:
        raise HTTPException(status_code=404, detail="Source not found")
    
    return _data_sources[source_id]


@router.delete("/sources/{source_id}")
async def delete_source(source_id: str):
    """
    Delete a data source and its chunks from the knowledge base.
    """
    if source_id not in _data_sources:
        raise HTTPException(status_code=404, detail="Source not found")
    
    try:
        from core.knowledge import get_knowledge_store
        
        source = _data_sources[source_id]
        knowledge_store = get_knowledge_store()
        
        # Delete chunks from store
        deleted_count = await knowledge_store.delete_by_source(source["filename"])
        
        # Remove from local tracking
        del _data_sources[source_id]
        
        return {
            "success": True,
            "deleted_chunks": deleted_count,
            "message": f"Source '{source['name']}' deleted"
        }
        
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_knowledge_stats():
    """
    Get statistics about the knowledge base.
    """
    try:
        from core.knowledge import get_knowledge_store
        
        knowledge_store = get_knowledge_store()
        stats = knowledge_store.get_stats()
        
        return KnowledgeStatsResponse(
            total_chunks=stats.get("total_chunks", 0),
            total_sources=len(_data_sources),
            domains=stats.get("domains", {}),
            regions=stats.get("regions", []),
            storage_path=stats.get("storage_path", "")
        )
        
    except Exception as e:
        logger.error(f"Stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview/{source_id}")
async def preview_source(source_id: str, limit: int = Query(10, ge=1, le=100)):
    """
    Preview chunks from a data source.
    """
    if source_id not in _data_sources:
        raise HTTPException(status_code=404, detail="Source not found")
    
    try:
        from core.knowledge import get_knowledge_store
        
        source = _data_sources[source_id]
        knowledge_store = get_knowledge_store()
        
        # Search for chunks from this source
        results = await knowledge_store.search(
            query=source["name"],
            n_results=limit
        )
        
        # Filter to only this source's chunks
        chunks = [
            {
                "id": r["id"],
                "content_preview": r["content"][:500],
                "metadata": r["metadata"]
            }
            for r in results
            if r.get("metadata", {}).get("source_name") == source["name"]
        ]
        
        return {
            "source": source,
            "chunks": chunks,
            "total_shown": len(chunks)
        }
        
    except Exception as e:
        logger.error(f"Preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
