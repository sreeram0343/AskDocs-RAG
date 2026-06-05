import logging
from typing import List, Dict, Any
from llama_index.core.schema import NodeWithScore
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage
from app.core.config import settings

logger = logging.getLogger("askdocs-rag.services.generator")

def generate_answer_with_citations(query: str, nodes: List[NodeWithScore]) -> Dict[str, Any]:
    """
    Generates an answer using gpt-4o-mini, enforcing that the response is based ONLY on the
    provided context nodes, and requiring inline citations for assertions (e.g. [Source: filename.pdf]).
    """
    logger.info("Starting query answer generation...")
    
    if not nodes:
        logger.warning("No context nodes provided. Returning default prompt-empty response.")
        return {
            "answer": "I cannot answer this question based on the provided documents as no relevant contexts were found.",
            "sources": []
        }

    # 1. format the contexts including metadata information
    context_blocks = []
    for i, node_with_score in enumerate(nodes):
        node = node_with_score.node
        # Extract filename (SimpleDirectoryReader populates this in metadata)
        file_name = node.metadata.get("file_name", "unknown_source")
        text = node.get_content(metadata_mode="none").strip()
        context_blocks.append(
            f"--- Document Chunk {i+1} [Source: {file_name}] ---\n"
            f"{text}\n"
        )
    
    formatted_context = "\n".join(context_blocks)

    # 2. Strict system prompt to instruct the LLM
    system_prompt = (
        "You are an expert, analytical AI assistant specializing in answering user queries using ONLY "
        "the provided document chunks. You must adhere to the following rules strictly:\n\n"
        "1. Answer the query using ONLY the facts and context provided in the document chunks. "
        "Do not make assumptions, extrapolate, or bring in outside knowledge.\n"
        "2. If the answer cannot be determined or found in the provided context, state clearly and politely: "
        "'I cannot answer this question based on the provided documents.' Do not attempt to guess.\n"
        "3. You MUST append an inline citation (e.g. [Source: filename.pdf] or [Source: readme.md]) "
        "whenever you make a claim or reference facts from a specific document chunk. "
        "Use the exact filename specified in the context block header [Source: <filename>].\n"
        "4. Be objective, concise, and professional."
    )

    user_prompt = (
        f"Context/Document Chunks:\n"
        f"{formatted_context}\n\n"
        f"User Query: {query}\n"
    )

    try:
        # 3. Configure LLM client
        llm = OpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.0  # Force deterministic, factually accurate answers
        )

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt)
        ]

        logger.info(f"Invoking {settings.LLM_MODEL} for answer generation...")
        response = llm.chat(messages)
        answer = response.message.content.strip()
        logger.info("Successfully generated answer.")

        # 4. Formulate response structure matching our QueryResponse Pydantic schema
        sources_payload = [
            {
                "node_id": node_with_score.node.node_id,
                "text": node_with_score.node.get_content(metadata_mode="none"),
                "score": float(node_with_score.score) if node_with_score.score is not None else 1.0,
                "metadata": node_with_score.node.metadata
            }
            for node_with_score in nodes
        ]

        return {
            "answer": answer,
            "sources": sources_payload
        }

    except Exception as e:
        logger.error(f"Error during LLM text generation: {str(e)}")
        return {
            "answer": "An error occurred while generating the answer. Please check your API key configuration or logs.",
            "sources": []
        }
