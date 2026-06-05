import logging
from fastapi import APIRouter, HTTPException, status
from app.services.evaluation import run_evaluation_pipeline

router = APIRouter()
logger = logging.getLogger("askdocs-rag.api.evaluate")

@router.post("/evaluate", status_code=status.HTTP_200_OK, tags=["admin"])
async def trigger_evaluation():
    """
    Triggers the automated evaluation pipeline to execute Faithfulness and Relevancy checks 
    over the mock dataset. Returns scoring results as JSON, suitable for hookups into CI/CD quality gates.
    """
    logger.info("REST endpoint `/evaluate` triggered.")
    try:
        report = await run_evaluation_pipeline()
        return report
    except Exception as e:
        logger.error(f"Failed to run evaluation endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while running the evaluation pipeline: {str(e)}"
        )
