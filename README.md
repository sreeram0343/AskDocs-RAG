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
├── docker-compose.yml    # Qdrant docker service configuration
├── requirements.txt      # Project dependencies
├── README.md             # Setup and developer documentation
└── app/
    ├── __init__.py       # App package initialization
    ├── main.py           # FastAPI entrypoint, middleware, and route mounting
    ├── api/              # API layer
    │   ├── __init__.py
    │   └── routes/       # Endpoint routers
    │       ├── __init__.py
    │       └── health.py # /health endpoint for server validation
    ├── core/             # Core application configs and settings
    │   ├── __init__.py
    │   └── config.py     # Pydantic-settings config validator
    └── services/         # Third-party integrations
        ├── __init__.py
        ├── llamaindex_service.py # LlamaIndex global configurations (LLM & Embed)
        └── qdrant_service.py     # Qdrant client connection manager
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
