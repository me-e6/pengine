# DataNarrative

**Intelligence-driven visual storytelling platform**

Transform raw data into compelling infographics through AI-powered analysis.

## 🎯 What It Does

DataNarrative answers 4 fundamental questions about any data:

1. **What is the data really saying?** (Semantic understanding)
2. **What changed meaningfully?** (Signal vs noise detection)
3. **Why does it matter to humans?** (Human impact translation)
4. **How should this be shown visually?** (Form follows reasoning)

## 🚀 Quick Start

```bash
# 1. Extract and enter directory
cd datanarrative

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run tests
python -m tests.test_ingest
python -m tests.test_knowledge
python -m tests.test_intelligence
python -m tests.test_renderer
python -m tests.test_api

# 5. Start API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## 📁 Project Structure

```
datanarrative/
├── api/                          # FastAPI Backend
│   ├── main.py                   # Application entry
│   └── routes/
│       ├── query.py              # NLP query processing
│       ├── ingest.py             # Data upload/ingestion
│       └── render.py             # Direct rendering
│
├── core/
│   ├── models.py                 # Data structures
│   │
│   ├── ingest/                   # Data Ingestion Pipeline
│   │   ├── parser.py             # CSV/Excel parsing
│   │   ├── chunker.py            # Smart data chunking
│   │   ├── tagger.py             # AI domain detection
│   │   └── pipeline.py           # Complete flow
│   │
│   ├── knowledge/                # Vector Knowledge Base
│   │   ├── embedder.py           # Text embeddings
│   │   ├── store.py              # ChromaDB storage
│   │   └── retriever.py          # RAG retrieval
│   │
│   ├── intelligence/             # The Brain
│   │   ├── analyzer.py           # Query understanding
│   │   ├── detector.py           # Insight detection
│   │   ├── narrator.py           # Story generation
│   │   └── reasoning.py          # Main orchestrator
│   │
│   └── renderer/                 # Visual Output
│       ├── base.py               # Foundation classes
│       ├── charts.py             # Matplotlib charts
│       ├── templates.py          # Template renderers
│       ├── story.py              # 5-frame stories
│       └── engine.py             # Render orchestrator
│
├── storage/
│   ├── uploads/                  # Uploaded data files
│   ├── outputs/                  # Generated images
│   └── chroma/                   # Vector database
│
├── tests/                        # Test suite
├── config.py                     # Configuration
└── requirements.txt              # Dependencies
```

## 🔥 Features

### Output Modes

| Mode | Description | When to Use |
|------|-------------|-------------|
| **Data Mode** | Single infographic | Facts, current state, comparisons |
| **Story Mode** | 5-frame narrative | Trends, changes over time |

### Story Mode Frames

1. **Context** - Where we started
2. **Change** - What happened
3. **Evidence** - The proof
4. **Consequence** - What it means
5. **Implication** - What's next

### Templates

| Template | Description | Best For |
|----------|-------------|----------|
| `hero_stat` | Large central number | Single metrics |
| `trend_line` | Line chart | Time series |
| `ranking_bar` | Horizontal bars | Rankings |
| `versus` | Side-by-side | Comparisons |
| `story_five_frame` | 5-panel story | Narratives |
| `story_carousel` | 5 separate images | Social media |

## 📡 API Endpoints

### Query
```bash
# Process natural language query
POST /api/v1/query
{
    "query": "How has literacy changed in Telangana?",
    "domain_hint": "education",
    "include_image": true
}

# Analyze query without results
GET /api/v1/query/analyze?q=...

# Get suggestions
GET /api/v1/query/suggestions
```

### Ingest
```bash
# Upload CSV/Excel
POST /api/v1/ingest/upload

# Manual data input
POST /api/v1/ingest/manual

# List sources
GET /api/v1/ingest/sources

# Knowledge stats
GET /api/v1/ingest/stats
```

### Render
```bash
# Render infographic
POST /api/v1/render/manual

# List templates
GET /api/v1/render/templates

# Quick render
POST /api/v1/render/quick?title=...&value=...&label=...
```

## 🎨 Domains & Colors

| Domain | Primary Color | Keywords |
|--------|--------------|----------|
| Education | Blue #3B82F6 | literacy, school, enrollment |
| Agriculture | Green #10B981 | crop, farmer, yield |
| Economy | Purple #8B5CF6 | GDP, income, tax |
| Health | Red #EF4444 | hospital, mortality |
| Infrastructure | Amber #F59E0B | roads, electricity |
| Environment | Emerald #059669 | forest, pollution |
| Demographics | Cyan #06B6D4 | population, census |
| Law | Slate #64748B | court, crime |

## 🧠 Intelligence Flow

```
User Query
    │
    ▼
┌─────────────────┐
│ Query Analyzer  │ → Intent, Topics, Locations, Time
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Retriever     │ → Relevant data from knowledge base
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Insight Detector│ → Growth, Decline, Ranking, Anomaly
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Narrator      │ → 5-frame story (if historical)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Render Engine  │ → PNG infographic
└─────────────────┘
```

## 📦 Dependencies

**Core:**
- Python 3.10+
- pandas, openpyxl
- matplotlib, pillow

**AI (optional):**
- anthropic (Claude API)
- sentence-transformers
- chromadb

**API:**
- fastapi
- uvicorn
- python-multipart

## 🔧 Configuration

Create `.env` from `.env.example`:

```env
# Optional: For AI-powered tagging
ANTHROPIC_API_KEY=your_key_here

# Storage paths
STORAGE_PATH=./storage
CHROMA_PATH=./storage/chroma

# API settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

## 📊 Sample Data

Included: `storage/uploads/telangana_education_2015_2023.csv`
- 40 rows of education data
- 10 districts × 4 years (2015-2023)
- Metrics: Literacy rate, Schools, Students, Teachers

## 🧪 Testing

```bash
# All tests
python -m tests.test_ingest      # Ingestion pipeline
python -m tests.test_knowledge   # Vector storage
python -m tests.test_intelligence # AI reasoning
python -m tests.test_renderer    # Image generation
python -m tests.test_api         # Full integration
```

## 📝 License

MIT License - Feel free to use and modify!

---

**Built with ❤️ for data-driven storytelling**
