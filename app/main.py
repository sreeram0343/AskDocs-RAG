import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Explicitly load environment variables from .env
load_dotenv()

from app.core.config import settings
from app.api.routes import health, ask, evaluate
from app.services.observability import setup_observability

# Setup global OpenTelemetry/Arize Phoenix observability tracing
setup_observability()

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("askdocs-rag")

# Initialize FastAPI application
app = FastAPI(
    title="AskDocs RAG API",
    description="Enterprise-grade Production RAG backend using FastAPI, LlamaIndex, and Qdrant",
    version="0.1.0"
)

# Configure CORS Middleware
# In production, specify actual allowed origins instead of "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)
app.include_router(ask.router)
app.include_router(evaluate.router)

@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint offering a welcome message and a link to the API documentation.
    """
    return {
        "message": "Welcome to AskDocs RAG API. Visit /docs for API documentation.",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
