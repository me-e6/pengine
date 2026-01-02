# DataNarrative API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
Currently no authentication required. Add API key header in production.

---

## Query Endpoints

### POST /query
Process a natural language query and generate an infographic.

**Request:**
```json
{
  "query": "How has literacy changed in Telangana from 2015 to 2023?",
  "domain_hint": "education",
  "force_mode": null,
  "include_image": true
}
```

**Response:**
```json
{
  "success": true,
  "query": "How has literacy changed in Telangana from 2015 to 2023?",
  "analysis": {
    "intent": "trend",
    "intent_confidence": 1.0,
    "topics": ["literacy"],
    "locations": ["Telangana"],
    "time_references": ["2015", "2023"],
    "domain_hint": "education",
    "requires_historical": true,
    "preferred_output": "story"
  },
  "output_mode": "story",
  "template_used": "story_five_frame",
  "insights": [
    {
      "type": "growth",
      "summary": "Literacy Rate increased by 7.6% from 2015 to 2023",
      "confidence": 0.85,
      "metric_name": "Literacy_Rate",
      "current_value": 89.5,
      "change_percentage": 7.6,
      "direction": "up",
      "sentiment": "positive"
    }
  ],
  "primary_insight": {...},
  "narrative_title": "Telangana's Literacy Revolution",
  "narrative_subtitle": "A decade of educational transformation",
  "narrative_frames": [
    {
      "type": "context",
      "headline": "Where We Started",
      "body_text": "In 2015, literacy stood at 66.5%",
      "key_metric": "66.5%",
      "key_metric_label": "2015 Literacy Rate"
    },
    ...
  ],
  "image_url": "/static/outputs/query_abc123.png",
  "image_id": "abc123",
  "sources_used": ["Census Data"],
  "confidence": 0.85,
  "processing_time_ms": 1234.5
}
```

### GET /query/analyze
Analyze a query without generating results.

**Query Parameters:**
- `q` (required): Query string

**Response:**
```json
{
  "query": "...",
  "normalized": "...",
  "intent": "trend",
  "intent_confidence": 1.0,
  "topics": ["literacy"],
  "locations": ["Telangana"],
  "time_references": ["2015", "2023"],
  "domain_hint": "education",
  "requires_historical": true,
  "search_keywords": ["literacy", "telangana"]
}
```

### GET /query/suggestions
Get suggested queries.

**Query Parameters:**
- `domain` (optional): Filter by domain

**Response:**
```json
{
  "suggestions": [
    "How has literacy changed in Telangana?",
    "Which district has the highest literacy rate?",
    ...
  ],
  "domain": "education"
}
```

---

## Render Endpoints

### POST /render/manual
Render an infographic with provided data.

**Request:**
```json
{
  "template": "hero_stat",
  "output_mode": "data",
  "title": "Telangana Literacy Rate",
  "subtitle": "2023 Census Data",
  "metrics": [
    {
      "value": 89.5,
      "label": "Literacy Rate",
      "change": 7.6,
      "unit": "%"
    }
  ],
  "insights": [
    "Highest rate in state history",
    "Urban areas lead with 92.8%"
  ],
  "domain": "education",
  "sentiment": "positive",
  "source": "Census 2023"
}
```

**Response:**
```json
{
  "success": true,
  "infogram_id": "abc123",
  "image_url": "/static/outputs/infogram_abc123.png",
  "template_used": "hero_stat",
  "width": 1080,
  "height": 1350,
  "render_time_ms": 156.3
}
```

### POST /render/quick
Quick render for simple metrics.

**Query Parameters:**
- `title` (required)
- `value` (required)
- `label` (required)
- `change` (optional)
- `domain` (default: "general")
- `template` (default: "hero_stat")

### GET /render/templates
List available templates.

**Response:**
```json
[
  {
    "id": "hero_stat",
    "name": "Hero Stat",
    "description": "Large central number with supporting context",
    "best_for": ["Single key metric", "Current state"]
  },
  ...
]
```

### PATCH /render/infogram/{id}/status
Update infogram approval status.

**Query Parameters:**
- `status` (required): "approved", "rejected", or "pending"
- `approved_by` (optional): Approver name

---

## Ingest Endpoints

### POST /ingest/upload
Upload a CSV/Excel file.

**Form Data:**
- `file`: The file to upload
- `source_name`: Name for this data source
- `domain_hint` (optional): Domain hint
- `description` (optional): Description

**Response:**
```json
{
  "success": true,
  "file_id": "abc123",
  "filename": "data.csv",
  "source_name": "Census Data",
  "tables_found": 1,
  "chunks_created": 6,
  "chunks_stored": 6,
  "domains_detected": ["education"],
  "has_historical_data": true,
  "time_range": [2015, 2023],
  "regions_detected": ["Telangana"],
  "processing_time_seconds": 1.23,
  "errors": [],
  "warnings": []
}
```

### POST /ingest/manual
Ingest data directly as JSON.

**Request:**
```json
{
  "source_name": "Quick Data",
  "data": [
    {"district": "Hyderabad", "literacy": 89.5, "year": 2023},
    {"district": "Warangal", "literacy": 86.5, "year": 2023}
  ],
  "domain": "education"
}
```

### GET /ingest/sources
List data sources.

### GET /ingest/stats
Get knowledge base statistics.

### DELETE /ingest/sources/{id}
Delete a data source.

---

## Utility Endpoints

### GET /health
Health check.

### GET /api/v1/config
Get public configuration.

---

## Templates Reference

| Template | Output Mode | Description |
|----------|-------------|-------------|
| `hero_stat` | data | Large central number |
| `trend_line` | data | Line chart for trends |
| `ranking_bar` | data | Horizontal bar ranking |
| `versus` | data | Side-by-side comparison |
| `story_five_frame` | story | 5-panel narrative |
| `story_carousel` | story | 5 separate images |

---

## Error Responses

All errors return:
```json
{
  "success": false,
  "error": "Error message",
  "status_code": 400
}
```

Common status codes:
- `400`: Bad request
- `404`: Not found
- `500`: Server error
