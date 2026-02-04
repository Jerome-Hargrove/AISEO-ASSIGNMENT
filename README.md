# SEO Article Generator

An AI-powered backend service that generates SEO-optimized articles by analyzing search engine results and producing publish-ready content.

## 🌟 Features

- **SERP Analysis** - Fetches and analyzes top 10 search results using SerpAPI
- **Intelligent Outline Generation** - Creates structured outlines based on competitive analysis
- **Full Article Generation** - Produces complete articles with proper heading hierarchy
- **SEO Optimization** - Title tags, meta descriptions, keyword placement, internal/external linking
- **Quality Scoring** - Validates content against SEO best practices (85+ quality score)
- **Job Management** - Track, pause, and resume generation jobs with SQLite persistence
- **Resume Capability** - Recover from failures using checkpoints
- **Streamlit GUI** - Easy-to-use web interface for generating articles

## 📋 Requirements

- Python 3.10+
- OpenAI API key
- SerpAPI key (optional - falls back to mock data)

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/liqteq/AISEO-Assignment.git
cd AISEO-Assignment

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```env
OPENAI_API_KEY=your_openai_api_key_here
SERPAPI_API_KEY=your_serpapi_key_here  # Optional
```

### 3. Run the Application

**Option A: API Server Only**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Option B: Streamlit GUI (Recommended)**
```bash
# Terminal 1: Start API server
uvicorn app.main:app --reload

# Terminal 2: Start Streamlit GUI
streamlit run streamlit_app.py
```

Access the applications:
- **Streamlit GUI**: http://localhost:8501
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

---

## 📝 Example Usage

### Input

```json
{
  "topic": "best productivity tools for remote teams",
  "target_word_count": 1500,
  "language": "en"
}
```

### Output

```json
{
  "job_id": "15eaa67a-5f09-40c3-a6b1-2e48f4346aa5",
  "status": "completed",
  "progress_percentage": 100,
  "result": {
    "title": "10 Best Productivity Tools for Remote Teams in 2025",
    "introduction": "In the evolving landscape of remote work, productivity tools have become essential...",
    "sections": [
      {
        "heading": "Video and Audio Calls",
        "heading_level": "h2",
        "content": "Communication is the backbone of any remote team..."
      },
      {
        "heading": "File Collaboration",
        "heading_level": "h2",
        "content": "Seamless file sharing and real-time collaboration..."
      },
      {
        "heading": "Google Workspace",
        "heading_level": "h2",
        "content": "Google Workspace provides a comprehensive suite..."
      },
      {
        "heading": "Project Management",
        "heading_level": "h2",
        "content": "Keeping projects on track requires robust tools..."
      }
    ],
    "conclusion": "In summary, productivity tools for remote teams are the cornerstone of effective collaboration...",
    "faq_section": [
      {
        "question": "What remote work tools have truly improved your workflow?",
        "answer": "Slack has significantly improved our remote team's workflow by providing real-time communication..."
      },
      {
        "question": "What are the best collaboration tools for remote teams?",
        "answer": "Some of the best collaboration tools include Slack, Zoom, Trello, Google Drive, and Asana..."
      },
      {
        "question": "What are the top remote team management tools?",
        "answer": "The top remote team management tools include Slack for communication, Trello for project management..."
      }
    ],
    "seo_metadata": {
      "title_tag": "Best Productivity Tools for Remote Teams 2025",
      "meta_description": "Discover the best productivity tools for remote teams to enhance collaboration and communication.",
      "primary_keyword": "best productivity tools for remote teams"
    },
    "keyword_analysis": {
      "primary_keyword": "best productivity tools for remote teams",
      "primary_keyword_count": 2,
      "primary_keyword_density": 0.45,
      "keyword_in_title": true,
      "keyword_in_intro": true
    },
    "internal_links": [
      {
        "anchor_text": "Video and Audio Calls",
        "target_topic": "Best Video and Audio Call Tools for Remote Teams",
        "context": "One of the key aspects of remote work is maintaining communication..."
      },
      {
        "anchor_text": "Google Workspace",
        "target_topic": "Maximizing Google Workspace for Remote Work",
        "context": "Many remote teams find that Google Workspace provides a comprehensive suite..."
      }
    ],
    "external_references": [
      {
        "source_name": "Forbes",
        "source_type": "article",
        "citation_context": "An article detailing the best productivity tools for remote teams..."
      },
      {
        "source_name": "Harvard Business Review",
        "source_type": "article",
        "citation_context": "Discussing the importance of using productivity tools..."
      }
    ],
    "total_word_count": 2795,
    "reading_time_minutes": 13,
    "quality_score": 85.0,
    "passes_quality_check": true
  }
}
```

---

## 🖥️ Streamlit GUI

The Streamlit interface provides an easy way to interact with the API:

![Streamlit GUI](docs/streamlit_screenshot.png)

### Features:
- **Generate Article** - Submit new article generation jobs
- **All Jobs** - View and manage all jobs, resume failed ones
- **View Article** - Read generated articles with quality metrics
- **Download** - Export articles as Markdown

### Running Streamlit:
```bash
# Make sure API server is running first!
streamlit run streamlit_app.py
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/generate` | Submit new article generation job |
| `GET` | `/jobs/{job_id}` | Get job status and result |
| `POST` | `/jobs/{job_id}/resume` | Resume a failed job |
| `GET` | `/jobs` | List all jobs (optionally filter by status) |
| `DELETE` | `/jobs/{job_id}` | Delete a job |
| `GET` | `/health` | Health check |

### cURL Examples

**Submit a job:**
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "best productivity tools for remote teams", "target_word_count": 1500}'
```

**Check job status:**
```bash
curl http://localhost:8000/jobs/{job_id}
```

**List all jobs:**
```bash
curl http://localhost:8000/jobs
```

---

## 📁 Project Structure

```
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── models/
│   │   ├── serp.py          # SERP data models
│   │   ├── article.py       # Article & SEO models
│   │   └── job.py           # Job management models
│   ├── services/
│   │   ├── serp_service.py  # SERP fetching/analysis
│   │   ├── agent.py         # Main orchestrating agent
│   │   ├── outline_generator.py
│   │   ├── article_generator.py
│   │   ├── quality_scorer.py
│   │   └── job_manager.py   # SQLite persistence
│   ├── api/routes.py        # REST endpoints
│   └── utils/
│       ├── llm_client.py    # OpenAI wrapper
│       └── validators.py    # SEO validators
├── tests/                   # Test suite (43 tests)
├── data/                    # SQLite database
├── streamlit_app.py         # Streamlit GUI
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing
```

**Test Results:**
```
======================= 43 passed in 1.06s ========================
```

---

## ⚙️ Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `OPENAI_MODEL` | Model to use (default: gpt-4) | No |
| `SERPAPI_API_KEY` | SerpAPI key for real SERP data | No |
| `DATABASE_URL` | SQLite path (default: sqlite:///./data/jobs.db) | No |
| `DEBUG` | Enable debug mode | No |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, etc.) | No |

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Streamlit GUI  │────▶│   FastAPI API   │────▶│   SQLite DB     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Content Agent  │
                        └─────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │ SERP Service│    │  Outline    │    │  Article    │
    │ (SerpAPI)   │    │  Generator  │    │  Generator  │
    └─────────────┘    └─────────────┘    └─────────────┘
           │                   │                   │
           └───────────────────┼───────────────────┘
                               ▼
                        ┌─────────────────┐
                        │ Quality Scorer  │
                        └─────────────────┘
```

---

## 📄 License

MIT License

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
