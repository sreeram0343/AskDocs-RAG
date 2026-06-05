# AskDocs-RAG API Backend

An enterprise-ready, modular RAG (Retrieval-Augmented Generation) backend API built with FastAPI, LlamaIndex, Qdrant, and OpenAI.

---

## 🏗️ Project Architecture & Structure

This project follows a clean, modular structure separating configurations, core logic, API routes, data schemas, and external services.

```text
askdocs-rag/
├── .env                  # Local environment configurations (ignored by git)
├── .env.example          # Environment variable template
├── .gitignore            # Git ignore patterns for Python, virtual envs, etc.
├── Dockerfile            # Production multi-stage Docker build configuration
├── docker-compose.yml    # Local Qdrant Docker Compose configuration
├── docker-compose.prod.yml # Production multi-service orchestration Compose
├── requirements.txt      # Project dependencies
├── README.md             # Setup and developer documentation
├── ingest.py             # CLI wrapper to trigger complete RAG indexing
├── sync.py               # CLI wrapper to trigger incremental RAG document syncs
├── evaluate.py           # CLI wrapper to run Faithfulness & Relevancy evaluations
├── .github/
│   └── workflows/
│       └── deploy.yml    # CI/CD Quality Gate & Docker Build pipeline
└── app/
    ├── __init__.py       # App package initialization
    ├── main.py           # FastAPI entrypoint, middleware, and route mounting
    ├── api/              # API controllers & routing
    │   ├── __init__.py
    │   └── routes/       # Endpoint routers
    │       ├── __init__.py
    │       ├── health.py # /health endpoint for server validation
    │       ├── ask.py    # POST /ask RAG query endpoint with cache/RBAC filters
    │       ├── auth.py   # POST /auth/token JWT token generator route
    │       └── evaluate.py # POST /evaluate admin test runner route
    ├── core/             # Core application configs and settings
    │   ├── __init__.py
    │   └── config.py     # Pydantic-settings config validator
    ├── models/           # Data definitions
    │   ├── __init__.py
    │   └── schemas.py    # QueryRequest, QueryResponse, SourceNode schemas
    └── services/         # Orchestrations and client connections
        ├── __init__.py
        ├── llamaindex_service.py # LlamaIndex global configurations
        ├── qdrant_service.py     # Qdrant client connection manager
        ├── ingestion.py          # Semantic splitter and folder reader
        ├── database.py           # Qdrant vector store and index indexer
        ├── retriever.py          # Hybrid retriever and BGE reranker
        ├── generator.py          # openai-mini generator with citations
        ├── cache_config.py       # cosine-similarity semantic query cache
        ├── evaluation.py         # LlamaIndex judges test runner
        └── observability.py      # Arize Phoenix tracer provider hook
```

---

## 🛠️ Prerequisites

Make sure you have the following installed on your machine:
- **Python** (version 3.10 or higher)
- **Docker & Docker Compose** (for running Qdrant locally)
- **Git**

---

## 🚀 Setup & Run Instructions

Follow these step-by-step commands to get the application up and running.

### 1. Clone & Initialize Git Repository (if not already done)
```bash
git clone https://github.com/sreeram0343/AskDocs-RAG.git
cd AskDocs-RAG
```

### 2. Set Up the Environment Configuration
Copy the `.env.example` file to `.env`:
```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# macOS / Linux (Bash)
cp .env.example .env
```
Open `.env` and fill in your actual `OPENAI_API_KEY`.

### 3. Spin Up Qdrant (Docker)
Ensure Docker is running, then start the Qdrant container:
```bash
docker compose up -d
```
*Verify that Qdrant is running by visiting http://localhost:6333 in your browser (shows a standard JSON dashboard).*

### 4. Create and Activate Virtual Environment
Create a virtual environment to manage dependencies locally:
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

### 5. Install Dependencies
Install all required libraries:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Run the FastAPI Development Server
Start the development server with live reload enabled:
```bash
python app/main.py
```
Or use Uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📊 API Verification

Once the server has started, verify the endpoints:
- **Server Root Info:** http://localhost:8000/
- **Health Check:** http://localhost:8000/health
- **Interactive Swagger Documentation:** http://localhost:8000/docs
- **Redoc Documentation:** http://localhost:8000/redoc
