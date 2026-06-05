import logging
from typing import Dict, Any, List
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.memory import ChatMemoryBuffer
from app.services.database import get_existing_index
from app.services.tools import custom_tools

logger = logging.getLogger("askdocs-rag.services.agent_engine")

# Session cache: session_id -> ReActAgent
agent_sessions: Dict[str, ReActAgent] = {}

def get_sub_question_query_engine() -> SubQuestionQueryEngine:
    """
    Initializes a SubQuestionQueryEngine to break down complex queries
    into parallelizable sub-questions and synthesize the answers.
    """
    logger.info("Initializing SubQuestionQueryEngine...")
    
    # 1. Fetch vector store index
    index = get_existing_index()
    
    # 2. Configure the default retriever-based query engine
    base_query_engine = index.as_query_engine(
        similarity_top_k=5,
        vector_store_query_mode="hybrid"
    )
    
    # 3. Define it as a QueryEngineTool
    base_tool = QueryEngineTool(
        query_engine=base_query_engine,
        metadata=ToolMetadata(
            name="askdocs_knowledge_base_retriever",
            description="Searches the AskDocs knowledge base. Returns contextual chunks from files."
        )
    )
    
    # 4. Construct SubQuestionQueryEngine using default OpenAI question generator
    # Automatically references the globally configured Settings.llm (gpt-4o-mini)
    sub_question_engine = SubQuestionQueryEngine.from_defaults(
        query_engine_tools=[base_tool],
        verbose=True
    )
    
    logger.info("SubQuestionQueryEngine successfully created.")
    return sub_question_engine

def get_or_create_agent(session_id: str) -> ReActAgent:
    """
    Gets or initializes a ReAct agent session with Conversational memory.
    Equips the agent with:
    1. RAG Router Query Engine (access to database via hybrid search or sub-questions).
    2. Datetime tool.
    3. Mathematical calculator tool.
    """
    if session_id in agent_sessions:
        return agent_sessions[session_id]

    logger.info(f"Creating new ReActAgent session: '{session_id}'")
    
    # Local import to prevent circular dependencies
    from app.services.router import get_router_query_engine
    
    # 1. Build the router engine
    router_engine = get_router_query_engine()
    
    # 2. Wrap the router engine as a query tool
    rag_tool = QueryEngineTool(
        query_engine=router_engine,
        metadata=ToolMetadata(
            name="rag_knowledge_base",
            description=(
                "Queries the AskDocs knowledge base. Use this tool to look up "
                "any facts, document contents, policies, manuals, or configuration guides. "
                "Input should be the natural language question."
            )
        )
    )
    
    # 3. Collect all tools (rag + math calculator + current datetime)
    tools = [rag_tool] + custom_tools
    
    # 4. Initialize sliding window token memory buffer
    memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
    
    # 5. Build ReAct agent
    agent = ReActAgent.from_tools(
        tools=tools,
        memory=memory,
        verbose=True
    )
    
    agent_sessions[session_id] = agent
    return agent
