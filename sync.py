import os
import sys
import logging
from dotenv import load_dotenv

# Load environment configurations
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("askdocs-rag.sync_cli")

# Ensure the app folder is in the Python search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.sync_pipeline import sync_documents

def run_sync():
    logger.info("=== Starting Data Incremental Sync CLI ===")
    try:
        # Trigger the sync pipeline
        result = sync_documents()
        
        status = result.get("status", "unknown")
        print("\n" + "=" * 50)
        print("             INCREMENTAL SYNC REPORT")
        print("=" * 50)
        print(f"Sync Status  : {status.upper()}")
        
        if status == "synchronized":
            processed = result.get("processed", [])
            deleted = result.get("deleted", [])
            print(f"Processed Files ({len(processed)}):")
            for f in processed:
                print(f"  + INDEXED/UPDATED: {f}")
            print(f"Deleted Files ({len(deleted)}):")
            for f in deleted:
                print(f"  - DELETED/PURGED: {f}")
        elif status == "up_to_date":
            print("No file changes detected since the last run. Vector store is in sync.")
        elif status == "empty_directory":
            print("Data directory is empty. Place some PDF/Markdown files inside 'data/' folder.")
            
        print("=" * 50 + "\n")
        
    except Exception as e:
        logger.error(f"Incremental Sync CLI execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_sync()
