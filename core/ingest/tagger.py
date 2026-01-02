"""
Domain Tagger
=============
Uses AI (Claude) to automatically detect domain, extract entities,
and add semantic metadata to data chunks.

This is the "understanding" layer before storage.
"""

import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# Optional anthropic import
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

from .chunker import DataChunkRaw
from ..models import DataChunk, Domain

logger = logging.getLogger(__name__)


@dataclass
class TaggingResult:
    """Result of AI tagging"""
    domain: Domain
    confidence: float
    entities: List[str]
    topics: List[str]
    summary: str
    year: Optional[int]
    region: Optional[str]
    data_quality: str  # "high", "medium", "low"


class DomainTagger:
    """
    AI-powered tagger that adds semantic metadata to chunks.
    
    Uses Claude to:
    - Detect the domain (education, agriculture, etc.)
    - Extract named entities (places, organizations, metrics)
    - Identify topics and themes
    - Generate a summary for retrieval
    - Detect year/period and region
    """
    
    TAGGING_PROMPT = """Analyze this data chunk and extract metadata.

DATA CHUNK:
{content}

COLUMN NAMES: {columns}

SAMPLE DATA (first few rows):
{sample_data}

Analyze and return a JSON object with:
{{
    "domain": "education|agriculture|economy|health|infrastructure|environment|demographics|law|other",
    "confidence": 0.0-1.0,
    "entities": ["list of important named entities: places, organizations, metrics, programs"],
    "topics": ["list of 3-5 key topics this data covers"],
    "summary": "2-3 sentence summary of what this data represents",
    "year": null or integer year if the data is about a specific year,
    "region": null or string if data is about a specific region (e.g., "Telangana", "Hyderabad"),
    "data_quality": "high|medium|low"
}}

Domain definitions:
- education: schools, literacy, enrollment, students, teachers, universities
- agriculture: crops, farmers, yield, irrigation, MSP, harvest, rainfall
- economy: GDP, income, tax, budget, revenue, growth, inflation, employment
- health: hospitals, doctors, disease, mortality, birth, vaccination, healthcare
- infrastructure: roads, electricity, water, housing, construction, transport
- environment: forest, pollution, climate, wildlife, conservation
- demographics: population, census, age, gender, urban, rural, migration
- law: courts, cases, crime, police, legislation, policy

Return ONLY valid JSON, no other text."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize tagger with Claude API.
        
        Args:
            api_key: Anthropic API key (uses env var if not provided)
        """
        self.client = None
        self.api_key = api_key
        self._init_client()
    
    def _init_client(self):
        """Initialize Anthropic client"""
        if not ANTHROPIC_AVAILABLE:
            logger.info("Anthropic not installed - using rule-based tagging only")
            self.client = None
            return
            
        try:
            if self.api_key:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            else:
                self.client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var
        except Exception as e:
            logger.warning(f"Could not initialize Claude client: {e}")
            self.client = None
    
    def tag_chunk(self, chunk: DataChunkRaw) -> TaggingResult:
        """
        Tag a single chunk with AI.
        
        Falls back to rule-based tagging if AI is unavailable.
        """
        if self.client:
            try:
                return self._ai_tag(chunk)
            except Exception as e:
                logger.warning(f"AI tagging failed, using fallback: {e}")
                return self._rule_based_tag(chunk)
        else:
            return self._rule_based_tag(chunk)
    
    def tag_chunks(self, chunks: List[DataChunkRaw]) -> List[DataChunk]:
        """
        Tag multiple chunks and convert to full DataChunk objects.
        """
        tagged_chunks = []
        
        for chunk in chunks:
            try:
                result = self.tag_chunk(chunk)
                
                # Convert to full DataChunk
                data_chunk = DataChunk(
                    id=chunk.chunk_id,
                    content=chunk.content,
                    content_type=chunk.content_type,
                    source_file=chunk.source_file,
                    source_name=chunk.source_table,
                    domain=result.domain,
                    year=result.year,
                    year_range=chunk.time_range,
                    region=result.region,
                    entities=result.entities,
                    columns=chunk.columns,
                    data_rows=chunk.data_rows,
                    has_historical_depth=chunk.has_time_dimension
                )
                
                tagged_chunks.append(data_chunk)
                
            except Exception as e:
                logger.error(f"Failed to tag chunk {chunk.chunk_id}: {e}")
                # Create chunk with minimal tagging
                data_chunk = DataChunk(
                    id=chunk.chunk_id,
                    content=chunk.content,
                    content_type=chunk.content_type,
                    source_file=chunk.source_file,
                    source_name=chunk.source_table,
                    domain=Domain.OTHER,
                    columns=chunk.columns,
                    data_rows=chunk.data_rows,
                    has_historical_depth=chunk.has_time_dimension
                )
                tagged_chunks.append(data_chunk)
        
        return tagged_chunks
    
    def _ai_tag(self, chunk: DataChunkRaw) -> TaggingResult:
        """Use Claude to tag the chunk"""
        
        # Prepare sample data
        sample_data = ""
        if chunk.data_rows:
            for i, row in enumerate(chunk.data_rows[:3]):
                row_str = " | ".join(f"{k}: {v}" for k, v in list(row.items())[:6])
                sample_data += f"Row {i+1}: {row_str}\n"
        
        prompt = self.TAGGING_PROMPT.format(
            content=chunk.content[:2000],  # Limit content length
            columns=", ".join(chunk.columns[:15]),
            sample_data=sample_data
        )
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response
        response_text = response.content[0].text.strip()
        
        # Clean up response if it has markdown
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        result = json.loads(response_text)
        
        # Map domain string to enum
        domain_str = result.get("domain", "other").lower()
        try:
            domain = Domain(domain_str)
        except ValueError:
            domain = Domain.OTHER
        
        return TaggingResult(
            domain=domain,
            confidence=result.get("confidence", 0.5),
            entities=result.get("entities", []),
            topics=result.get("topics", []),
            summary=result.get("summary", ""),
            year=result.get("year"),
            region=result.get("region"),
            data_quality=result.get("data_quality", "medium")
        )
    
    def _rule_based_tag(self, chunk: DataChunkRaw) -> TaggingResult:
        """
        Fallback rule-based tagging when AI is unavailable.
        Uses keyword matching to determine domain.
        """
        
        # Combine all text for analysis
        text = f"{chunk.content} {' '.join(chunk.columns)} {' '.join(chunk.key_entities)}"
        text_lower = text.lower()
        
        # Domain keywords (from config)
        domain_keywords = {
            Domain.EDUCATION: ["school", "literacy", "enrollment", "student", "teacher", "college", "university", "education"],
            Domain.AGRICULTURE: ["crop", "farmer", "yield", "irrigation", "msp", "harvest", "soil", "rainfall", "agriculture", "farm"],
            Domain.ECONOMY: ["gdp", "income", "tax", "budget", "revenue", "expenditure", "growth", "inflation", "economy", "economic"],
            Domain.HEALTH: ["hospital", "doctor", "patient", "disease", "mortality", "birth", "vaccination", "health", "medical"],
            Domain.INFRASTRUCTURE: ["road", "bridge", "electricity", "water", "sanitation", "housing", "construction", "infrastructure"],
            Domain.ENVIRONMENT: ["forest", "pollution", "air", "climate", "temperature", "wildlife", "environment", "conservation"],
            Domain.DEMOGRAPHICS: ["population", "census", "age", "gender", "urban", "rural", "migration", "density", "demographic"],
            Domain.LAW: ["court", "case", "crime", "police", "judgment", "legislation", "policy", "legal", "law"],
        }
        
        # Count keyword matches
        scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[domain] = score
        
        # Determine domain
        if scores:
            domain = max(scores, key=scores.get)
            confidence = min(scores[domain] / 5, 1.0)  # Normalize confidence
        else:
            domain = Domain.OTHER
            confidence = 0.1
        
        # Extract year from content
        year = self._extract_year(text)
        
        # Extract region
        region = self._extract_region(text)
        
        return TaggingResult(
            domain=domain,
            confidence=confidence,
            entities=chunk.key_entities[:10],
            topics=[],
            summary=f"Data from {chunk.source_table}",
            year=year,
            region=region,
            data_quality="medium"
        )
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from text using regex"""
        import re
        
        # Look for 4-digit years (1900-2099)
        years = re.findall(r'\b((?:19|20)\d{2})\b', text)
        if years:
            # Return the most recent year
            year_ints = [int(y) for y in years]
            return max(year_ints)
        return None
    
    def _extract_region(self, text: str) -> Optional[str]:
        """Extract region from text"""
        text_lower = text.lower()
        
        # Indian states/regions to look for
        regions = [
            "Telangana", "Andhra Pradesh", "Karnataka", "Tamil Nadu", "Kerala",
            "Maharashtra", "Gujarat", "Rajasthan", "Uttar Pradesh", "Bihar",
            "West Bengal", "Odisha", "Madhya Pradesh", "Chhattisgarh",
            "Hyderabad", "Bangalore", "Chennai", "Mumbai", "Delhi",
            "India", "National"
        ]
        
        for region in regions:
            if region.lower() in text_lower:
                return region
        
        return None


# === Convenience functions ===

def tag_chunks_with_ai(
    chunks: List[DataChunkRaw], 
    api_key: Optional[str] = None
) -> List[DataChunk]:
    """Quick tagging function"""
    tagger = DomainTagger(api_key=api_key)
    return tagger.tag_chunks(chunks)


def detect_domain(text: str) -> Domain:
    """Quick domain detection from text"""
    tagger = DomainTagger()
    # Create a minimal chunk for detection
    chunk = DataChunkRaw(
        chunk_id="temp",
        content=text,
        content_type="text",
        source_table="",
        source_file="",
        columns=[],
        data_rows=[],
        row_count=0,
        has_time_dimension=False,
        time_column=None,
        time_range=None,
        key_entities=[],
        numeric_highlights={},
        chunk_index=0,
        total_chunks=1
    )
    result = tagger._rule_based_tag(chunk)
    return result.domain
