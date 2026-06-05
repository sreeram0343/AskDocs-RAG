import logging
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from app.core.config import settings

logger = logging.getLogger("askdocs-rag.services.llamaindex")

class LlamaIndexService:
    def __init__(self):
        self.initialize_settings()

    def initialize_settings(self):
        """
        Configures global LlamaIndex settings such as the default LLM and embedding models.
        """
        try:
            logger.info("Configuring LlamaIndex LLM and Embedding models...")
            
            # 1. Set global LLM (e.g. gpt-4o-mini)
            Settings.llm = OpenAI(
                model=settings.LLM_MODEL,
                api_key=settings.OPENAI_API_KEY
            )
            
            # 2. Set global Embedding Model (e.g. text-embedding-3-small)
            Settings.embed_model = OpenAIEmbedding(
                model=settings.EMBEDDING_MODEL,
                api_key=settings.OPENAI_API_KEY
            )
            
            logger.info("LlamaIndex settings configured successfully.")
        except Exception as e:
            logger.error(f"Error configuring LlamaIndex settings: {str(e)}")

# Global service instance
llamaindex_service = LlamaIndexService()
