import time
import logging
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from app.services.auth import get_current_user
from app.services.agent_engine import get_or_create_agent
from app.services.fallback import check_and_log_fallback

router = APIRouter()
logger = logging.getLogger("askdocs-rag.api.agent")

class AgentChatRequest(BaseModel):
    message: str = Field(..., description="Message/query to send to the conversational agent", example="Compare our 2024 compliance policy with 2026 updates.")
    session_id: str = Field(default="default_session", description="Conversation session ID to maintain history")

class AgentChatResponse(BaseModel):
    response: str = Field(..., description="The agent's reply")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted source nodes if RAG retrieval was executed")
    execution_time_ms: float = Field(..., description="API execution latency in milliseconds")

@router.post("/agent/chat", response_model=AgentChatResponse, status_code=status.HTTP_200_OK, tags=["agent"])
async def agent_chat(
    request: AgentChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Agentic Conversational RAG Endpoint:
    1. Fetches or initializes a ReAct agent session using session_id (linked to username).
    2. Runs the query through the agent loops (supporting tools like RAG query, calculations, datetimes).
    3. Handles fallbacks and logging if the agent replies that it cannot find the information.
    4. Measures latency and returns the conversational response.
    """
    message = request.message.strip()
    session_id = f"{current_user['username']}_{request.session_id}"
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty."
        )
        
    logger.info(f"Agent Chat: User '{current_user['username']}' (Session: '{session_id}'): '{message}'")
    start_time = time.perf_counter()
    
    try:
        # Get or create the ReAct agent instance for this session
        agent = get_or_create_agent(session_id)
        
        # Send message to agent
        agent_response = agent.chat(message)
        
        # Extract sources from RAG tool execution outputs if called
        sources = []
        rag_was_called = False
        
        for source in agent_response.sources:
            if source.tool_name == "rag_knowledge_base":
                rag_was_called = True
                raw_out = source.raw_output
                if raw_out and hasattr(raw_out, "source_nodes"):
                    for node_with_score in raw_out.source_nodes:
                        sources.append({
                            "node_id": node_with_score.node.node_id,
                            "text": node_with_score.node.get_content(metadata_mode="none"),
                            "score": float(node_with_score.score) if node_with_score.score is not None else 1.0,
                            "metadata": node_with_score.node.metadata
                        })
                        
        execution_time_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Apply graceful fallback check & logging
        # If RAG was called, pass sources count; otherwise default to 1 so we don't trigger fallback
        # (the agent might have answered using other tools like math/date)
        sources_count = len(sources) if rag_was_called else 1
        
        clean_answer = check_and_log_fallback(
            query=message,
            answer=agent_response.response,
            sources_count=sources_count
        )
        
        return AgentChatResponse(
            response=clean_answer,
            sources=sources,
            execution_time_ms=execution_time_ms
        )
        
    except Exception as e:
        logger.error(f"Error during agent chat execution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while executing the chat agent: {str(e)}"
        )
