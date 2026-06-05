from pydantic import BaseModel, Field
from typing import List, Dict, Any

class QueryRequest(BaseModel):
    query: str = Field(
        ..., 
        description="The question or search query for the RAG pipeline", 
        json_schema_extra={"example": "How do I configure hybrid search with Qdrant?"}
    )

class SourceNode(BaseModel):
    node_id: str = Field(..., description="Unique ID of the source node chunk")
    text: str = Field(..., description="Text content of the retrieved chunk")
    score: float = Field(..., description="Relevance score after retrieval and reranking")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary containing file_name, file_path, etc.")

class QueryResponse(BaseModel):
    answer: str = Field(..., description="The generated answer from LLM with inline citations")
    sources: List[SourceNode] = Field(default_factory=list, description="List of source document chunks used to answer the query")
    execution_time_ms: float = Field(..., description="End-to-end processing execution time in milliseconds")
    cache_hit: bool = Field(..., description="True if the response was retrieved from the semantic cache")

