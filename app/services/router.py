import logging
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from app.services.database import get_existing_index

logger = logging.getLogger("askdocs-rag.services.router")

def get_router_query_engine() -> RouterQueryEngine:
    """
    Builds and returns a RouterQueryEngine that routes queries to either:
    1. Direct Hybrid Search (for simple queries).
    2. Sub-Question Query Engine (for complex multi-hop comparisons).
    """
    logger.info("Initializing RouterQueryEngine...")
    
    # Resolve circular dependency by doing a local import
    from app.services.agent_engine import get_sub_question_query_engine
    
    # 1. Fetch the existing VectorStoreIndex
    index = get_existing_index()
    
    # 2. Define simple direct query engine tool
    direct_query_engine = index.as_query_engine(
        similarity_top_k=5,
        vector_store_query_mode="hybrid"
    )
    direct_tool = QueryEngineTool(
        query_engine=direct_query_engine,
        metadata=ToolMetadata(
            name="direct_hybrid_search",
            description=(
                "Performs a quick direct keyword and semantic search. "
                "Best for simple queries, specific factual lookups, or keyword searches."
            )
        )
    )
    
    # 3. Fetch sub-question reasoning query engine tool
    sub_question_engine = get_sub_question_query_engine()
    sub_question_tool = QueryEngineTool(
        query_engine=sub_question_engine,
        metadata=ToolMetadata(
            name="multi_hop_sub_question_reasoning",
            description=(
                "Decomposes complex, comparative, multi-part, or time-spanning queries "
                "into simpler sub-questions, executes them in parallel, and synthesizes "
                "the results. Best for queries comparing documents, versions, or different facts."
            )
        )
    )
    
    # 4. Initialize Router with a Single LLM Selector
    # This automatically uses gpt-4o-mini configured globally in llamaindex_service.py
    router_engine = RouterQueryEngine(
        selector=LLMSingleSelector.from_defaults(),
        query_engine_tools=[direct_tool, sub_question_tool]
    )
    
    logger.info("RouterQueryEngine successfully configured.")
    return router_engine
