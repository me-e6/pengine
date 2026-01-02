"""
Query Analyzer
==============
Understands user queries and extracts intent, entities, and context.
This is the first step in the intelligence pipeline.
"""

import re
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """What the user wants to know"""
    TREND = "trend"              # How has X changed over time?
    COMPARISON = "comparison"    # Compare X vs Y
    RANKING = "ranking"          # What are the top/bottom X?
    CURRENT_STATE = "current"    # What is X now?
    BREAKDOWN = "breakdown"      # What makes up X?
    CORRELATION = "correlation"  # Is X related to Y?
    ANOMALY = "anomaly"          # What's unusual about X?
    GENERAL = "general"          # General information request


@dataclass
class QueryAnalysis:
    """Result of analyzing a user query"""
    original_query: str
    normalized_query: str
    
    # Intent
    intent: QueryIntent
    intent_confidence: float
    
    # Extracted entities
    topics: List[str]           # Main subjects (e.g., "literacy", "enrollment")
    locations: List[str]        # Places mentioned (e.g., "Telangana", "Hyderabad")
    time_references: List[str]  # Time periods (e.g., "2023", "last 5 years")
    metrics: List[str]          # Specific metrics (e.g., "rate", "percentage")
    
    # Inferred context
    domain_hint: Optional[str] = None
    requires_historical: bool = False
    requires_comparison: bool = False
    
    # Output preference
    preferred_output: str = "data"  # "story" or "data"
    
    # For search
    search_keywords: List[str] = field(default_factory=list)


class QueryAnalyzer:
    """
    Analyzes natural language queries to understand user intent.
    
    Uses pattern matching and keyword extraction.
    Can be enhanced with Claude for complex queries.
    """
    
    # Intent patterns
    INTENT_PATTERNS = {
        QueryIntent.TREND: [
            r'\b(trend|change|changed|grow|grew|increase|decrease|rise|fall|over time|over the years|evolution)\b',
            r'\b(how has|how did|what happened to)\b.*\b(over|since|from)\b',
        ],
        QueryIntent.COMPARISON: [
            r'\b(compare|comparison|versus|vs|differ|difference|between)\b',
            r'\b(better|worse|higher|lower|more|less) than\b',
        ],
        QueryIntent.RANKING: [
            r'\b(top|bottom|best|worst|highest|lowest|most|least|rank|ranking)\b',
            r'\b(which|what).*(most|least|highest|lowest)\b',
        ],
        QueryIntent.CURRENT_STATE: [
            r'\b(current|now|today|present|latest|recent)\b',
            r'\b(what is|what are|how much|how many)\b(?!.*\b(change|trend|over)\b)',
        ],
        QueryIntent.BREAKDOWN: [
            r'\b(breakdown|composition|distribution|split|makeup|consist)\b',
            r'\b(what makes up|composed of|divided into)\b',
        ],
        QueryIntent.CORRELATION: [
            r'\b(correlat|relat|connect|link|affect|impact|influence)\b',
            r'\b(does|is).*\b(affect|impact|relate)\b',
        ],
        QueryIntent.ANOMALY: [
            r'\b(unusual|anomal|outlier|unexpected|surprising|strange)\b',
            r'\b(what.*(wrong|odd|different))\b',
        ],
    }
    
    # Domain keywords
    DOMAIN_KEYWORDS = {
        'education': ['school', 'literacy', 'student', 'teacher', 'enrollment', 'education', 'college', 'university', 'exam', 'dropout'],
        'agriculture': ['crop', 'farm', 'farmer', 'yield', 'irrigation', 'harvest', 'agriculture', 'msp', 'rainfall', 'soil'],
        'economy': ['gdp', 'income', 'tax', 'budget', 'revenue', 'growth', 'inflation', 'employment', 'economy', 'investment'],
        'health': ['hospital', 'doctor', 'patient', 'disease', 'mortality', 'birth', 'vaccination', 'health', 'medical', 'death'],
        'infrastructure': ['road', 'bridge', 'electricity', 'water', 'sanitation', 'housing', 'construction', 'infrastructure', 'transport'],
        'environment': ['forest', 'pollution', 'air', 'climate', 'temperature', 'wildlife', 'environment', 'conservation', 'carbon'],
        'demographics': ['population', 'census', 'age', 'gender', 'urban', 'rural', 'migration', 'density', 'demographic'],
        'law': ['court', 'case', 'crime', 'police', 'judgment', 'legislation', 'policy', 'legal', 'law', 'justice'],
    }
    
    # Location patterns (Indian states/cities)
    LOCATIONS = [
        'telangana', 'andhra pradesh', 'karnataka', 'tamil nadu', 'kerala',
        'maharashtra', 'gujarat', 'rajasthan', 'uttar pradesh', 'bihar',
        'hyderabad', 'bangalore', 'chennai', 'mumbai', 'delhi',
        'warangal', 'karimnagar', 'nizamabad', 'khammam', 'adilabad',
        'india', 'national', 'state', 'district'
    ]
    
    # Time patterns
    TIME_PATTERNS = [
        r'\b(19|20)\d{2}\b',                    # Years: 2015, 2023
        r'\b(last|past|previous)\s+\d+\s+(year|month|decade)s?\b',  # last 5 years
        r'\b(since|from|after|before)\s+(19|20)\d{2}\b',  # since 2015
        r'\b(this|current|last)\s+(year|month|quarter)\b',  # this year
        r'\bfy\s*\d{2,4}\b',                    # FY2023
    ]
    
    def __init__(self):
        # Compile patterns for efficiency
        self.intent_compiled = {
            intent: [re.compile(p, re.IGNORECASE) for p in patterns]
            for intent, patterns in self.INTENT_PATTERNS.items()
        }
        self.time_compiled = [re.compile(p, re.IGNORECASE) for p in self.TIME_PATTERNS]
    
    def analyze(self, query: str) -> QueryAnalysis:
        """
        Analyze a user query.
        
        Args:
            query: Natural language query
            
        Returns:
            QueryAnalysis with extracted information
        """
        # Normalize
        normalized = self._normalize(query)
        
        # Detect intent
        intent, confidence = self._detect_intent(normalized)
        
        # Extract entities
        topics = self._extract_topics(normalized)
        locations = self._extract_locations(normalized)
        time_refs = self._extract_time_references(query)  # Use original for years
        metrics = self._extract_metrics(normalized)
        
        # Infer domain
        domain = self._infer_domain(normalized, topics)
        
        # Determine if historical data needed
        requires_historical = (
            intent == QueryIntent.TREND or
            len(time_refs) >= 2 or
            any(word in normalized for word in ['change', 'trend', 'over time', 'growth', 'decline'])
        )
        
        # Determine if comparison needed
        requires_comparison = (
            intent == QueryIntent.COMPARISON or
            intent == QueryIntent.RANKING or
            'vs' in normalized or 'versus' in normalized or 'compare' in normalized
        )
        
        # Determine preferred output mode
        preferred_output = "story" if requires_historical else "data"
        
        # Build search keywords
        search_keywords = self._build_search_keywords(topics, locations, metrics)
        
        return QueryAnalysis(
            original_query=query,
            normalized_query=normalized,
            intent=intent,
            intent_confidence=confidence,
            topics=topics,
            locations=locations,
            time_references=time_refs,
            metrics=metrics,
            domain_hint=domain,
            requires_historical=requires_historical,
            requires_comparison=requires_comparison,
            preferred_output=preferred_output,
            search_keywords=search_keywords
        )
    
    def _normalize(self, query: str) -> str:
        """Normalize query text"""
        text = query.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\-]', '', text)
        return text
    
    def _detect_intent(self, query: str) -> Tuple[QueryIntent, float]:
        """Detect the primary intent of the query"""
        scores = {}
        
        for intent, patterns in self.intent_compiled.items():
            score = 0
            for pattern in patterns:
                if pattern.search(query):
                    score += 1
            if score > 0:
                scores[intent] = score
        
        if not scores:
            return QueryIntent.GENERAL, 0.5
        
        best_intent = max(scores, key=scores.get)
        max_possible = len(self.intent_compiled[best_intent])
        confidence = min(scores[best_intent] / max_possible, 1.0)
        
        return best_intent, confidence
    
    def _extract_topics(self, query: str) -> List[str]:
        """Extract main topics from query"""
        topics = []
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for kw in keywords:
                if kw in query and kw not in topics:
                    topics.append(kw)
        return topics[:5]
    
    def _extract_locations(self, query: str) -> List[str]:
        """Extract location references"""
        found = []
        for loc in self.LOCATIONS:
            if loc in query:
                found.append(loc.title())
        return found
    
    def _extract_time_references(self, query: str) -> List[str]:
        """Extract time references"""
        refs = []
        years = re.findall(r'\b(20[0-2]\d|19\d{2})\b', query)
        refs.extend(years)
        return list(set(refs))
    
    def _extract_metrics(self, query: str) -> List[str]:
        """Extract metric-related terms"""
        metric_keywords = [
            'rate', 'percentage', 'percent', 'ratio', 'count', 'number',
            'total', 'average', 'mean', 'median', 'growth', 'decline'
        ]
        return [m for m in metric_keywords if m in query]
    
    def _infer_domain(self, query: str, topics: List[str]) -> Optional[str]:
        """Infer the domain from query and topics"""
        domain_scores = {}
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query or kw in topics)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        return None
    
    def _build_search_keywords(
        self, 
        topics: List[str], 
        locations: List[str],
        metrics: List[str]
    ) -> List[str]:
        """Build effective search keywords"""
        keywords = []
        keywords.extend(topics)
        keywords.extend([loc.lower() for loc in locations])
        keywords.extend([m for m in metrics if m not in ['rate', 'percentage', 'number']])
        return keywords[:10]


def analyze_query(query: str) -> QueryAnalysis:
    """Quick analysis function"""
    analyzer = QueryAnalyzer()
    return analyzer.analyze(query)
