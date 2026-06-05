import logging
import asyncio
from typing import List, Dict, Any
from llama_index.core.base.response.schema import Response
from llama_index.core.evaluation import FaithfulnessEvaluator, RelevancyEvaluator
from app.services.retriever import retrieve_relevant_nodes
from app.services.generator import generate_answer_with_citations

logger = logging.getLogger("askdocs-rag.services.evaluation")

# Mock evaluation dataset
EVAL_DATASET = [
    {
        "query": "How do I configure hybrid search with Qdrant?",
        "ground_truth": "Initialize QdrantVectorStore with enable_hybrid=True."
    },
    {
        "query": "What are the requirements for local Qdrant Vector DB?",
        "ground_truth": "Qdrant runs locally using Docker on port 6333 (HTTP) and 6334 (gRPC) with volume mapping to ./qdrant_storage."
    },
    {
        "query": "What models are configured in Phase 1 setup?",
        "ground_truth": "Phase 1 configuration uses text-embedding-3-small for embeddings and gpt-4o-mini for the LLM."
    },
    {
        "query": "How do I run the data ingestion and indexing pipeline?",
        "ground_truth": "Run the data ingestion and indexing pipeline using python ingest.py."
    },
    {
        "query": "What is the endpoint to check API server health?",
        "ground_truth": "The endpoint to verify API server health is /health."
    }
]

async def run_evaluation_pipeline() -> Dict[str, Any]:
    """
    Asynchronously executes the evaluation pipeline.
    It feeds the queries through the RAG pipeline, then uses LLM evaluators
    to check Faithfulness (no hallucinations) and Relevancy.
    """
    logger.info("Initializing LlamaIndex evaluators...")
    try:
        # Faithfulness checks if response is supported by retrieved contexts
        faithfulness_eval = FaithfulnessEvaluator()
        # Relevancy checks if response matches query and context
        relevancy_eval = RelevancyEvaluator()
    except Exception as e:
        logger.error(f"Failed to initialize evaluators: {str(e)}")
        raise e

    results = []
    total_faithfulness = 0.0
    total_relevancy = 0.0
    valid_evaluations = 0

    logger.info(f"Running evaluation on {len(EVAL_DATASET)} queries...")

    for i, item in enumerate(EVAL_DATASET):
        query = item["query"]
        ground_truth = item["ground_truth"]
        
        logger.info(f"[{i+1}/{len(EVAL_DATASET)}] Evaluating query: '{query}'")
        
        try:
            # 1. Retrieve nodes
            nodes = retrieve_relevant_nodes(query)
            
            # 2. Generate RAG answer
            rag_output = generate_answer_with_citations(query, nodes)
            answer = rag_output["answer"]
            
            # 3. Create LlamaIndex Response object
            response_obj = Response(
                response=answer,
                source_nodes=[n for n in nodes]
            )
            
            # 4. Run evaluators asynchronously
            logger.info("Running Faithfulness and Relevancy checks...")
            faith_result = await faithfulness_eval.aevaluate_response(response=response_obj)
            rel_result = await relevancy_eval.aevaluate_response(query=query, response=response_obj)
            
            # Extract scores
            faith_score = float(faith_result.score) if faith_result.score is not None else (1.0 if faith_result.passing else 0.0)
            rel_score = float(rel_result.score) if rel_result.score is not None else (1.0 if rel_result.passing else 0.0)
            
            total_faithfulness += faith_score
            total_relevancy += rel_score
            valid_evaluations += 1
            
            results.append({
                "query": query,
                "ground_truth": ground_truth,
                "generated_answer": answer,
                "faithfulness": {
                    "score": faith_score,
                    "passing": faith_result.passing,
                    "feedback": faith_result.feedback
                },
                "relevancy": {
                    "score": rel_score,
                    "passing": rel_result.passing,
                    "feedback": rel_result.feedback
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to evaluate query '{query}': {str(e)}")
            results.append({
                "query": query,
                "ground_truth": ground_truth,
                "error": str(e)
            })

    # Compute averages
    avg_faithfulness = (total_faithfulness / valid_evaluations) if valid_evaluations > 0 else 0.0
    avg_relevancy = (total_relevancy / valid_evaluations) if valid_evaluations > 0 else 0.0

    summary = {
        "metrics": {
            "average_faithfulness": avg_faithfulness,
            "average_relevancy": avg_relevancy,
            "total_queries_tested": len(EVAL_DATASET),
            "successful_evaluations": valid_evaluations
        },
        "details": results
    }

    logger.info("Evaluation run finished.")
    return summary
