import logging
import threading
import numpy as np
from typing import Dict, Any, List, Optional
from llama_index.embeddings.openai import OpenAIEmbedding
from app.core.config import settings

logger = logging.getLogger("askdocs-rag.services.cache")

class SemanticCache:
    def __init__(self, threshold: float = 0.95):
        """
        Initializes an in-memory Semantic Cache with a cosine similarity threshold.
        """
        self.threshold = threshold
        self.cache: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._embed_model = None

    @property
    def embed_model(self):
        """
        Lazily initialize the OpenAI embedding client.
        """
        if self._embed_model is None:
            self._embed_model = OpenAIEmbedding(
                model=settings.EMBEDDING_MODEL,
                api_key=settings.OPENAI_API_KEY
            )
        return self._embed_model

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Computes cosine similarity between two float vectors.
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        return float(dot_product / (norm_v1 * norm_v2))

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a cached response if the incoming query is semantically similar
        to an existing query above the configured threshold.
        """
        cleaned_query = query.strip()
        if not cleaned_query:
            return None

        # Lock-free check if cache is empty to avoid embedding call overhead
        with self._lock:
            if not self.cache:
                return None

        try:
            logger.info(f"Generating query embedding for semantic cache lookup: '{cleaned_query}'")
            query_embedding = self.embed_model.get_query_embedding(cleaned_query)
            
            best_sim = -1.0
            best_match = None
            
            with self._lock:
                for item in self.cache:
                    sim = self._cosine_similarity(query_embedding, item["embedding"])
                    if sim > best_sim:
                        best_sim = sim
                        best_match = item
            
            if best_sim >= self.threshold and best_match is not None:
                logger.info(f"Semantic Cache HIT! Similarity: {best_sim:.4f} >= {self.threshold}")
                return best_match["response"]
                
            logger.info(f"Semantic Cache MISS. Highest similarity: {best_sim:.4f} < {self.threshold}")
            
        except Exception as e:
            logger.error(f"Error checking semantic cache: {str(e)}")
            
        return None

    def set(self, query: str, response: Dict[str, Any]):
        """
        Caches the response along with the generated query embedding.
        """
        cleaned_query = query.strip()
        if not cleaned_query:
            return

        try:
            logger.info(f"Caching result for query: '{cleaned_query}'")
            query_embedding = self.embed_model.get_query_embedding(cleaned_query)
            
            with self._lock:
                # Add copy of response to avoid mutation issues
                self.cache.append({
                    "query": cleaned_query,
                    "embedding": query_embedding,
                    "response": dict(response)
                })
            logger.info(f"Cached response. Current cache size: {len(self.cache)}")
        except Exception as e:
            logger.error(f"Error saving to semantic cache: {str(e)}")

# Instantiate the global semantic cache singleton
semantic_cache = SemanticCache()
