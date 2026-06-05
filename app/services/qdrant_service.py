import logging
from qdrant_client import QdrantClient
from app.core.config import settings

logger = logging.getLogger("askdocs-rag.services.qdrant")

class QdrantService:
    def __init__(self):
        self.client = None
        self.initialize_client()

    def initialize_client(self):
        """
        Initializes the connection to the Qdrant Vector DB instance.
        """
        try:
            logger.info(f"Connecting to Qdrant at {settings.QDRANT_URL}...")
            # Initialize connection to local docker or cloud Qdrant instance
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
            )
            logger.info("Successfully connected to Qdrant.")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant connection: {str(e)}")
            # We don't raise here so the app can still start even if database is offline, 
            # but in production you might want to retry or crash depending on requirements.
            self.client = None

# Global service instance
qdrant_service = QdrantService()
