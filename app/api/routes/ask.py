import time
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import QueryRequest, QueryResponse
from app.services.retriever import retrieve_relevant_nodes
from app.services.generator import generate_answer_with_citations
from app.services.cache_config import semantic_cache
from app.services.auth import get_current_user

router = APIRouter()
logger = logging.getLogger("askdocs-rag.api.ask")

@router.post("/ask", response_model=QueryResponse, status_code=status.HTTP_200_OK, tags=["query"])
async def ask_question(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    RAG Query Pipeline:
    1. Checks the semantic cache for highly similar queries.
    2. If miss, triggers Hybrid Search in Qdrant (top 15 results), filtering by RBAC user role.
    3. Reranks nodes down to 5 using BAAI/bge-reranker-base.
    4. Prompts gpt-4o-mini to generate an answer backed strictly by the contexts with inline source citations.
    5. Caches the response and returns payload with execution latency.
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )
        
    logger.info(f"Processing query request from user '{current_user['username']}' (role: {current_user['role']}): '{query}'")
    start_time = time.perf_counter()
    
    try:
        # Step 1: Check semantic cache
        cached_result = semantic_cache.get(query)
        if cached_result is not None:
            execution_time_ms = (time.perf_counter() - start_time) * 1000.0
            return QueryResponse(
                answer=cached_result["answer"],
                sources=cached_result["sources"],
                execution_time_ms=execution_time_ms,
                cache_hit=True
            )
            
        # Step 2 & 3: Retrieve the top semantically relevant nodes and rerank them (passing RBAC role filter)
        nodes = retrieve_relevant_nodes(query, role=current_user["role"])
        
        # Step 4: Call LLM to generate the answer with citations
        result = generate_answer_with_citations(query, nodes)
        
        execution_time_ms = (time.perf_counter() - start_time) * 1000.0
        
        response_payload = {
            "answer": result["answer"],
            "sources": result["sources"],
            "execution_time_ms": execution_time_ms,
            "cache_hit": False
        }
        
        # Step 5: Save result to cache
        semantic_cache.set(query, response_payload)
        
        return QueryResponse(**response_payload)
        
    except Exception as e:
        logger.error(f"Failed to execute RAG query pipeline: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred during query execution: {str(e)}"
        )

