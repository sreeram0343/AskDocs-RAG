import logging
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import QueryRequest, QueryResponse
from app.services.retriever import retrieve_relevant_nodes
from app.services.generator import generate_answer_with_citations

router = APIRouter()
logger = logging.getLogger("askdocs-rag.api.ask")

@router.post("/ask", response_model=QueryResponse, status_code=status.HTTP_200_OK, tags=["query"])
async def ask_question(request: QueryRequest):
    """
    RAG Query Pipeline:
    1. Triggers Hybrid Search in Qdrant (top 15 results).
    2. Reranks nodes down to 5 using BAAI/bge-reranker-base.
    3. Prompts gpt-4o-mini to generate an answer backed strictly by the contexts with inline source citations.
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )
        
    logger.info(f"Processing query request: '{query}'")
    
    try:
        # Step 1 & 2: Retrieve the top semantically relevant nodes and rerank them
        nodes = retrieve_relevant_nodes(query)
        
        # Step 3: Call LLM to generate the answer with citations
        result = generate_answer_with_citations(query, nodes)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute RAG query pipeline: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred during query execution: {str(e)}"
        )
