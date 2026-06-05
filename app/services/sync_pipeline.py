import os
import json
import hashlib
import logging
from typing import Dict, Any, List, Set
from qdrant_client.http import models as qdrant_models
from llama_index.core import SimpleDirectoryReader
from app.core.config import settings
from app.services.database import get_vector_store, create_and_persist_index
from app.services.qdrant_service import qdrant_service

logger = logging.getLogger("askdocs-rag.services.sync")
STATE_FILE_PATH = "storage/sync_state.json"

def calculate_file_hash(file_path: str) -> str:
    """
    Computes MD5 hash of a file to detect content modifications.
    """
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def load_sync_state() -> Dict[str, Any]:
    """
    Loads document synchronization logs from local json state file.
    """
    if not os.path.exists(STATE_FILE_PATH):
        os.makedirs(os.path.dirname(STATE_FILE_PATH), exist_ok=True)
        return {"files": {}}
    try:
        with open(STATE_FILE_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load sync state: {str(e)}")
        return {"files": {}}

def save_sync_state(state: Dict[str, Any]):
    """
    Persists document synchronization logs to local json state file.
    """
    try:
        os.makedirs(os.path.dirname(STATE_FILE_PATH), exist_ok=True)
        with open(STATE_FILE_PATH, 'w') as f:
            json.dump(state, f, indent=2)
        logger.info("Sync state file updated successfully.")
    except Exception as e:
        logger.error(f"Failed to save sync state file: {str(e)}")

def delete_nodes_from_qdrant(node_ids: List[str]):
    """
    Removes vector nodes directly from Qdrant by point IDs (UUIDs).
    """
    if not node_ids:
        return
        
    logger.info(f"Removing {len(node_ids)} stale points from Qdrant...")
    try:
        if qdrant_service.client:
            qdrant_service.client.delete(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points_selector=qdrant_models.PointIdsList(
                    points=node_ids
                )
            )
            logger.info("Stale points deleted successfully from Qdrant.")
        else:
            logger.error("Qdrant client not initialized. Cannot delete nodes.")
    except Exception as e:
        logger.error(f"Failed to delete points from Qdrant: {str(e)}")

def sync_documents(data_dir: str = "data") -> Dict[str, Any]:
    """
    Incremental Syncing Pipeline:
    1. Scans data/ directories.
    2. Identifies new, modified, and deleted files using MD5 hashes.
    3. Purges deleted file nodes from Qdrant and updates sync state.
    4. Computes semantic chunks and registers new/modified nodes.
    """
    logger.info("=== Initializing Incremental Document Sync Pipeline ===")
    
    # 1. Load sync logs
    state = load_sync_state()
    cached_files = state.get("files", {})
    
    if not os.path.exists(data_dir):
        logger.info(f"Data directory '{data_dir}' not found. Creating empty data directory.")
        os.makedirs(data_dir)
        return {"status": "empty_directory"}
        
    # 2. Scan data folder for PDF and Markdown files
    current_files = []
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith((".pdf", ".md")):
                current_files.append(os.path.join(root, file))
                
    current_files_set = set(current_files)
    cached_files_set = set(cached_files.keys())
    
    # Identify new, deleted and modified files
    new_files = current_files_set - cached_files_set
    deleted_files = cached_files_set - current_files_set
    
    modified_files = set()
    for f in current_files_set & cached_files_set:
        current_hash = calculate_file_hash(f)
        if current_hash != cached_files[f]["hash"]:
            modified_files.add(f)
            
    logger.info(f"Scan analysis: {len(new_files)} new, {len(modified_files)} modified, {len(deleted_files)} deleted.")
    
    # 3. Handle Deleted Files
    for f in deleted_files:
        logger.info(f"File deleted locally. Purging from Qdrant: '{f}'")
        old_ids = cached_files[f].get("node_ids", [])
        delete_nodes_from_qdrant(old_ids)
        del cached_files[f]
        
    # 4. Handle Modified Files (Delete old chunks first)
    for f in modified_files:
        logger.info(f"File contents changed. Purging old chunks from Qdrant: '{f}'")
        old_ids = cached_files[f].get("node_ids", [])
        delete_nodes_from_qdrant(old_ids)
        
    # Ingest new and modified files
    files_to_process = new_files | modified_files
    
    if not files_to_process:
        logger.info("No files modified or added. Vector store is up to date.")
        state["files"] = cached_files
        save_sync_state(state)
        return {"status": "up_to_date"}
        
    # Set up Semantic Splitter node parser
    from llama_index.core.node_parser import SemanticSplitterNodeParser
    from llama_index.embeddings.openai import OpenAIEmbedding
    
    embed_model = OpenAIEmbedding(
        model=settings.EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY
    )
    splitter = SemanticSplitterNodeParser(
        buffer_size=1,
        breakpoint_percentile_threshold=95,
        embed_model=embed_model
    )
    
    # 5. Process files incrementally
    for f in files_to_process:
        logger.info(f"Processing and chunking document: '{f}'")
        try:
            reader = SimpleDirectoryReader(input_files=[f])
            documents = reader.load_data()
            
            # Attach metadata (RBAC roles based on subdirectory)
            for doc in documents:
                doc.metadata["file_name"] = os.path.basename(f)
                normalized_path = f.replace("\\", "/").lower()
                
                # Assign security group requirements
                if "/hr/" in normalized_path:
                    doc.metadata["required_role"] = "hr"
                elif "/engineering/" in normalized_path:
                    doc.metadata["required_role"] = "engineering"
                else:
                    doc.metadata["required_role"] = "public"
            
            # Parse chunks using Semantic Splitter
            nodes = splitter.get_nodes_from_documents(documents)
            
            if nodes:
                # Add/persist nodes to Vector Store Index
                create_and_persist_index(nodes)
                
                # Update sync log state
                cached_files[f] = {
                    "hash": calculate_file_hash(f),
                    "node_ids": [node.node_id for node in nodes]
                }
                logger.info(f"Indexed document '{f}' successfully with {len(nodes)} chunks.")
            else:
                logger.warning(f"No chunks parsed from file '{f}'.")
                cached_files[f] = {
                    "hash": calculate_file_hash(f),
                    "node_ids": []
                }
                
        except Exception as e:
            logger.error(f"Failed to index file '{f}': {str(e)}")
            
    # Save current status
    state["files"] = cached_files
    save_sync_state(state)
    logger.info("=== Incremental Sync Completed Successfully ===")
    
    return {
        "status": "synchronized",
        "processed": list(files_to_process),
        "deleted": list(deleted_files)
    }
