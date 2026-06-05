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

---

## 🔄 Incremental Sync Pipeline

The project features a hash-based incremental syncing system that calculates MD5 checksums of files under the `data/` directory to manage Qdrant vectors efficiently.

- **Trigger Syncing**: Run the syncing CLI script:
  ```bash
  python sync.py
  ```
- **Tracking Log**: The system records the indexing state in `storage/sync_state.json`, including the associated file hash and mapped Qdrant node UUIDs.
- **Auto Cleanup**: Deleting or modifying a local file will automatically trigger the deletion of the old point vectors from your Qdrant collection during the next sync run.

---

## 🛰️ Observability & Tracing Dashboard

We utilize OpenTelemetry and **Arize Phoenix** to monitor and capture the RAG execution graphs.

- **Enable Observability**: Set `PHOENIX_ENABLE=true` in your `.env`.
- **View Dashboard**: Open your browser at http://localhost:6006 to explore the tracing dashboard.
- **Trace Metrics**: Automatically logs latency timelines, retrieval segments, token metrics, context chunks sent to the LLM, and output responses.

---

## 🔒 JWT Authentication & RBAC Filters

This project enforces Role-Based Access Control (RBAC) on the `/ask` endpoint to prevent data leaks.

- **Get a Token**: Send a POST request to `/auth/token` with a JSON body:
  ```json
  {
    "username": "sreeram",
    "role": "engineering"
  }
  ```
  *(Supported roles: `admin`, `engineering`, `hr`, `public`)*
- **Metadata Filters**: Chunks are automatically filtered in Qdrant based on folders:
  - Documents under `data/hr/` require the `hr` or `admin` role.
  - Documents under `data/engineering/` require the `engineering` or `admin` role.
  - Root documents are `public` and accessible by all roles.



