import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("askdocs-rag.ingest")

# Ensure the app folder is in the Python search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ingestion import load_and_chunk_documents
from app.services.database import create_and_persist_index

def run_ingestion():
    """
    Main execution pipeline for loading local documents,
    chunking them semantically, and indexing them to Qdrant Vector Database.
    """
    logger.info("=== Starting Data Ingestion and Indexing Pipeline ===")
    
    data_dir = "data"
    
    # 1. Create the data directory if it doesn't exist to avoid execution errors
    if not os.path.exists(data_dir):
        logger.info(f"Creating empty local data directory: '{data_dir}'")
        os.makedirs(data_dir)
        logger.info("Please place your PDF or Markdown documents in the 'data/' folder and rerun this script.")
        return

    # 2. Extract and semantically chunk PDF/Markdown files
    nodes = load_and_chunk_documents(data_dir=data_dir)
    
    if not nodes:
        logger.warning("Ingestion finished with 0 nodes. No files were processed.")
        return
        
    logger.info(f"Loaded and chunked {len(nodes)} document sections.")

    # 3. Create Vector Store Index and persist to Qdrant
    try:
        create_and_persist_index(nodes)
        logger.info("=== Ingestion and Indexing Pipeline Completed Successfully! ===")
    except Exception as e:
        logger.error(f"Ingestion and Indexing Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_ingestion()
