from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["system"])
async def health_check():
    """
    Health check endpoint to verify that the API is running.
    In the future, this can be expanded to check connections to
    Qdrant and OpenAI.
    """
    return {
        "status": "healthy",
        "service": "AskDocs-RAG API",
        "version": "0.1.0"
    }
