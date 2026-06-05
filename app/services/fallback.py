import os
import json
import logging
import datetime
from typing import Dict, Any, List

logger = logging.getLogger("askdocs-rag.services.fallback")
UNANSWERED_LOG_PATH = "logs/unanswered_queries.json"

def log_unanswered_query(query: str, reason: str, details: Dict[str, Any] = None):
    """
    Logs unanswered, low-confidence, or zero-chunk query events
    to a local log file, which serves as a backlog for administrators.
    """
    logger.info(f"Logging fallback event for query: '{query}' | Reason: {reason}")
    os.makedirs(os.path.dirname(UNANSWERED_LOG_PATH), exist_ok=True)
    
    new_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "query": query,
        "reason": reason,
        "details": details or {}
    }
    
    # Read existing entries
    entries = []
    if os.path.exists(UNANSWERED_LOG_PATH):
        try:
            with open(UNANSWERED_LOG_PATH, 'r') as f:
                entries = json.load(f)
                if not isinstance(entries, list):
                    entries = []
        except Exception as e:
            logger.error(f"Failed to read existing unanswered queries log: {str(e)}")
            entries = []
            
    # Append and persist
    entries.append(new_entry)
    try:
        with open(UNANSWERED_LOG_PATH, 'w') as f:
            json.dump(entries, f, indent=2)
        logger.info(f"Saved unanswered query log event. Total log size: {len(entries)}")
    except Exception as e:
        logger.error(f"Failed to write unanswered query logs: {str(e)}")

def check_and_log_fallback(query: str, answer: str, sources_count: int) -> str:
    """
    Checks if a generated response indicates a failure or low-confidence match.
    If so, it logs the event and returns a standard graceful fallback message.
    """
    fallback_message = "I cannot confidently find this in the current knowledge base."
    
    lower_answer = answer.lower()
    cannot_answer_phrases = [
        "cannot answer this question", 
        "do not have information", 
        "no relevant context",
        "i'm sorry, but",
        "based on the provided context, i cannot",
        "i cannot find",
        "i don't have access"
    ]
    
    is_fallback = False
    reason = ""
    
    # Case 1: No context chunks retrieved from vector store
    if sources_count == 0:
        is_fallback = True
        reason = "zero_chunks_retrieved"
        
    # Case 2: The LLM explicitly stated it couldn't answer from context
    elif any(phrase in lower_answer for phrase in cannot_answer_phrases):
        is_fallback = True
        reason = "low_llm_confidence_or_unanswered"
        
    if is_fallback:
        log_unanswered_query(
            query=query,
            reason=reason,
            details={"sources_count": sources_count, "original_response": answer}
        )
        return fallback_message
        
    return answer
