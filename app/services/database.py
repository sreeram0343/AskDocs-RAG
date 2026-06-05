import logging
from typing import List
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.schema import BaseNode
from llama_index.vector_stores.qdrant import QdrantVectorStore
from app.core.config import settings
from app.services.qdrant_service import qdrant_service

logger = logging.getLogger("askdocs-rag.services.database")

def get_vector_store(collection_name: str = None) -> QdrantVectorStore:
    """
    Constructs and returns a QdrantVectorStore with Hybrid Search enabled.
    """
    collection = collection_name or settings.QDRANT_COLLECTION_NAME
    
    if not qdrant_service.client:
        logger.error("Qdrant client is not initialized.")
        raise ConnectionError("Qdrant database is offline or client is uninitialized.")
        
    logger.info(f"Initializing QdrantVectorStore for collection '{collection}' with hybrid search enabled.")
    
    # Configure hybrid search using Qdrant's sparse vector capabilities
    # By default, LlamaIndex uses fastembed under the hood for sparse embeddings (BM42/BM25)
    return QdrantVectorStore(
        collection_name=collection,
        client=qdrant_service.client,
        enable_hybrid=True
    )

def create_and_persist_index(nodes: List[BaseNode], collection_name: str = None) -> VectorStoreIndex:
    """
    Accepts chunked nodes, builds a VectorStoreIndex, and persists it to Qdrant.
    """
    collection = collection_name or settings.QDRANT_COLLECTION_NAME
    logger.info(f"Persisting {len(nodes)} nodes to Qdrant collection: {collection}")
    
    try:
        vector_store = get_vector_store(collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        index = VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context,
            show_progress=True
        )
        
        logger.info(f"Successfully created and persisted index for collection '{collection}'.")
        return index
    except Exception as e:
        logger.error(f"Failed to create or persist index: {str(e)}")
        raise e

def get_existing_index(collection_name: str = None) -> VectorStoreIndex:
    """
    Binds to an existing Qdrant collection and returns a VectorStoreIndex.
    """
    collection = collection_name or settings.QDRANT_COLLECTION_NAME
    logger.info(f"Fetching existing index from Qdrant collection: {collection}")
    
    try:
        vector_store = get_vector_store(collection)
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        return index
    except Exception as e:
        logger.error(f"Failed to fetch existing index: {str(e)}")
        raise e
