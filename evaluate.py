import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("askdocs-rag.evaluate_cli")

# Ensure the app folder is in the Python search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.evaluation import run_evaluation_pipeline

async def run_cli():
    logger.info("=== Starting RAG Evaluation Script ===")
    try:
        # Execute the async evaluation runner
        report = await run_evaluation_pipeline()
        
        metrics = report["metrics"]
        print("\n" + "=" * 50)
        print("             EVALUATION REPORT SUMMARY")
        print("=" * 50)
        print(f"Total Queries Tested   : {metrics['total_queries_tested']}")
        print(f"Successful Evaluations : {metrics['successful_evaluations']}")
        print(f"Average Faithfulness   : {metrics['average_faithfulness']:.4f} (hallucination index)")
        print(f"Average Relevancy      : {metrics['average_relevancy']:.4f} (answer relevance)")
        print("=" * 50)
        
        # Print details of failing items if any
        for detail in report["details"]:
            if "error" in detail:
                print(f"FAIL Query: '{detail['query']}' | Error: {detail['error']}")
            else:
                faith = detail["faithfulness"]["score"]
                rel = detail["relevancy"]["score"]
                print(f"Query: '{detail['query']}'")
                print(f" -> Faithfulness: {faith:.2f} | Relevancy: {rel:.2f}")
        print("=" * 50 + "\n")
        
        # Enforce quality gates (e.g. at least 80% passing)
        if metrics["average_faithfulness"] >= 0.8 and metrics["average_relevancy"] >= 0.8:
            print("RAG Quality Gate Status: PASS")
            sys.exit(0)
        else:
            print("RAG Quality Gate Status: FAIL (Scores are below the 0.80 threshold)")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to execute evaluation CLI: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_cli())
