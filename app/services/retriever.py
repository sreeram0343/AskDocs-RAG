import logging
from typing import List
from llama_index.core.schema import NodeWithScore
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.postprocessor.sbert_rerank import SentenceTransformerRerank
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters, FilterCondition, FilterOperator
from app.services.database import get_existing_index

logger = logging.getLogger("askdocs-rag.services.retriever")

def retrieve_relevant_nodes(
    query: str, 
    role: str = "public", 
    similarity_top_k: int = 15, 
    rerank_top_n: int = 5
) -> List[NodeWithScore]:
    """
    Advanced retrieval pipeline:
    1. Builds dynamic metadata filters depending on user role (RBAC).
    2. Fetches the top similarity_top_k (default 15) nodes from Qdrant using Hybrid Search.
    3. Reranks the retrieved nodes down to rerank_top_n (default 5) using the BAAI/bge-reranker-base model.
    """
    logger.info(f"Initiating advanced retrieval for query: '{query}' | User Role: '{role}'")
    
    try:
        # Load the existing index referencing our Qdrant vector store
        index = get_existing_index()
        
        # Build allowed roles lists
        allowed_roles = ["public"]
        if role == "admin":
            allowed_roles = ["public", "admin", "hr", "engineering"]
        elif role in ("hr", "engineering"):
            allowed_roles.append(role)
            
        # Construct MetadataFilters container using OR condition so we match any allowed roles
        filters_list = [
            MetadataFilter(key="required_role", value=r, operator=FilterOperator.EQ)
            for r in allowed_roles
        ]
        metadata_filters = MetadataFilters(
            filters=filters_list,
            condition=FilterCondition.OR
        )
        
        # Configure retriever for hybrid query mode (dense + sparse search) with RBAC filters
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=similarity_top_k,
            vector_store_query_mode="hybrid",
            alpha=0.5,  # Balanced weight between vector (dense) and BM25 (sparse) searches
            filters=metadata_filters
        )
        
        # Retrieve the top 15 initial raw results
        logger.info(f"Querying Qdrant index (Hybrid Search, top_k={similarity_top_k})...")
        retrieved_nodes = retriever.retrieve(query)
        logger.info(f"Retrieved {len(retrieved_nodes)} raw nodes from Qdrant.")
        
        if not retrieved_nodes:
            logger.warning("No nodes retrieved from database.")
            return []
            
        # Rerank retrieved nodes using the cross-encoder reranker
        logger.info(f"Applying cross-encoder reranker (model='BAAI/bge-reranker-base', top_n={rerank_top_n})...")
        reranker = SentenceTransformerRerank(
            model="BAAI/bge-reranker-base",
            top_n=rerank_top_n
        )
        
        reranked_nodes = reranker.postprocess_nodes(retrieved_nodes, query_str=query)
        logger.info(f"Reranking completed. Top {len(reranked_nodes)} nodes selected.")
        return reranked_nodes
        
    except Exception as e:
        logger.error(f"Error in retrieval pipeline: {str(e)}")
        # In case of failure (like missing index or GPU/CUDA issues), return an empty list or fallback
        # depending on production requirements
        return []
