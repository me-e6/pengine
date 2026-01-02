"""
DataNarrative Configuration
===========================
Central configuration for the entire platform.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


# === Path Configuration ===
BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
ASSETS_DIR = BASE_DIR / "assets"
TEMPLATES_DIR = BASE_DIR / "templates"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Create a .env file in the project root with these values.
    """
    
    # === API Settings ===
    app_name: str = "DataNarrative"
    app_version: str = "0.1.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # === Claude API ===
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    claude_model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    
    # === Storage Paths ===
    chroma_persist_dir: str = str(STORAGE_DIR / "chroma")
    uploads_dir: str = str(STORAGE_DIR / "uploads")
    outputs_dir: str = str(STORAGE_DIR / "outputs")
    
    # === Knowledge Base ===
    collection_name: str = "datanarrative_knowledge"
    embedding_model: str = "all-MiniLM-L6-v2"  # Free, local, fast
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # === Rendering ===
    default_width: int = 1080
    default_height: int = 1350  # Instagram portrait
    story_width: int = 1080
    story_height: int = 1920   # Story format
    dpi: int = 150
    
    # === Branding ===
    brand_name: str = "DataNarrative"
    watermark_opacity: float = 0.7
    
    # === Regional Focus ===
    default_region: str = "Telangana"
    default_country: str = "India"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# === Singleton Instance ===
settings = Settings()


# === Domain Configuration ===
DOMAINS = {
    "education": {
        "name": "Education",
        "icon": "education.png",
        "color_primary": "#3B82F6",    # Blue
        "color_secondary": "#60A5FA",
        "keywords": ["school", "literacy", "enrollment", "student", "teacher", "college", "university"]
    },
    "agriculture": {
        "name": "Agriculture", 
        "icon": "agriculture.png",
        "color_primary": "#10B981",    # Green
        "color_secondary": "#34D399",
        "keywords": ["crop", "farmer", "yield", "irrigation", "msp", "harvest", "soil", "rainfall"]
    },
    "economy": {
        "name": "Economy",
        "icon": "economy.png",
        "color_primary": "#8B5CF6",    # Purple
        "color_secondary": "#A78BFA",
        "keywords": ["gdp", "income", "tax", "budget", "revenue", "expenditure", "growth", "inflation"]
    },
    "health": {
        "name": "Health",
        "icon": "health.png",
        "color_primary": "#EF4444",    # Red
        "color_secondary": "#F87171",
        "keywords": ["hospital", "doctor", "patient", "disease", "mortality", "birth", "vaccination"]
    },
    "infrastructure": {
        "name": "Infrastructure",
        "icon": "infrastructure.png",
        "color_primary": "#F59E0B",    # Amber
        "color_secondary": "#FBBF24",
        "keywords": ["road", "bridge", "electricity", "water", "sanitation", "housing", "construction"]
    },
    "environment": {
        "name": "Environment",
        "icon": "environment.png",
        "color_primary": "#059669",    # Emerald
        "color_secondary": "#10B981",
        "keywords": ["forest", "pollution", "air", "water", "climate", "temperature", "rainfall", "wildlife"]
    },
    "demographics": {
        "name": "Demographics",
        "icon": "demographics.png",
        "color_primary": "#06B6D4",    # Cyan
        "color_secondary": "#22D3EE",
        "keywords": ["population", "census", "age", "gender", "urban", "rural", "migration", "density"]
    },
    "law": {
        "name": "Law & Governance",
        "icon": "law.png",
        "color_primary": "#64748B",    # Slate
        "color_secondary": "#94A3B8",
        "keywords": ["court", "case", "crime", "police", "judgment", "legislation", "policy", "regulation"]
    }
}


# === Insight Types ===
INSIGHT_TYPES = {
    "growth": {
        "name": "Growth",
        "sentiment": "positive",
        "color": "#10B981",
        "description": "Increasing trend, improvement"
    },
    "decline": {
        "name": "Decline",
        "sentiment": "negative",
        "color": "#EF4444",
        "description": "Decreasing trend, deterioration"
    },
    "comparison": {
        "name": "Comparison",
        "sentiment": "neutral",
        "color": "#3B82F6",
        "description": "Side-by-side analysis"
    },
    "ranking": {
        "name": "Ranking",
        "sentiment": "neutral",
        "color": "#8B5CF6",
        "description": "Ordered list by value"
    },
    "distribution": {
        "name": "Distribution",
        "sentiment": "neutral",
        "color": "#06B6D4",
        "description": "Parts of a whole"
    },
    "correlation": {
        "name": "Correlation",
        "sentiment": "neutral",
        "color": "#F59E0B",
        "description": "Relationship between variables"
    },
    "anomaly": {
        "name": "Anomaly",
        "sentiment": "warning",
        "color": "#F59E0B",
        "description": "Unusual pattern or outlier"
    },
    "threshold": {
        "name": "Threshold",
        "sentiment": "warning",
        "color": "#EF4444",
        "description": "Critical level reached"
    }
}


# === Template Mapping ===
TEMPLATE_MAPPING = {
    # Insight type -> Best template
    "growth": ["trend_line", "hero_stat", "before_after"],
    "decline": ["trend_line", "hero_stat", "before_after"],
    "comparison": ["versus", "before_after", "ranking_bar"],
    "ranking": ["ranking_bar", "hero_stat"],
    "distribution": ["pie_breakdown", "ranking_bar"],
    "correlation": ["trend_line", "versus"],
    "anomaly": ["hero_stat", "trend_line"],
    "threshold": ["hero_stat", "trend_line"]
}


# === Ensure Directories Exist ===
def ensure_directories():
    """Create all required directories if they don't exist."""
    dirs = [
        STORAGE_DIR / "chroma",
        STORAGE_DIR / "uploads",
        STORAGE_DIR / "outputs",
        ASSETS_DIR / "fonts" / "primary",
        ASSETS_DIR / "fonts" / "secondary",
        ASSETS_DIR / "icons" / "sectors",
        ASSETS_DIR / "brand",
        ASSETS_DIR / "maps" / "telangana"
    ]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)


# Run on import
ensure_directories()
