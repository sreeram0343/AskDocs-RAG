import os
import logging
from typing import List
from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import BaseNode
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from app.core.config import settings

logger = logging.getLogger("askdocs-rag.services.ingestion")

def load_and_chunk_documents(data_dir: str = "data") -> List[BaseNode]:
    """
    Loads documents (PDFs and Markdown files) from a local directory,
    attaches standard metadata, and chunks them using LlamaIndex's
    SemanticSplitterNodeParser (using text-embedding-3-small).
    """
    if not os.path.exists(data_dir):
        logger.warning(f"Data directory '{data_dir}' does not exist. Creating it.")
        os.makedirs(data_dir)
        return []

    logger.info(f"Loading documents from local directory: {data_dir}")
    
    # 1. Load documents using SimpleDirectoryReader supporting .pdf and .md
    try:
        reader = SimpleDirectoryReader(
            input_dir=data_dir,
            recursive=True,
            required_exts=[".pdf", ".md"]
        )
        documents = reader.load_data()
    except Exception as e:
        logger.error(f"Error loading documents from '{data_dir}': {str(e)}")
        return []
    
    if not documents:
        logger.warning(f"No PDF or Markdown documents found in directory '{data_dir}'.")
        return []
        
    logger.info(f"Loaded {len(documents)} document pages/sections.")

    # 2. Attach and normalize metadata
    for doc in documents:
        # SimpleDirectoryReader automatically attaches file_path, but let's ensure file_name is present
        if "file_name" not in doc.metadata:
            file_path = doc.metadata.get("file_path", "")
            doc.metadata["file_name"] = os.path.basename(file_path) if file_path else "unknown_document"
            
    # 3. Setup Semantic Splitter
    logger.info("Initializing SemanticSplitterNodeParser with text-embedding-3-small...")
    try:
        embed_model = OpenAIEmbedding(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY
        )
        
        # Splitter that uses embedding similarity to identify breakpoints between sentences
        splitter = SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=95,
            embed_model=embed_model
        )
        
        # 4. Chunk documents
        logger.info("Splitting documents semantically...")
        nodes = splitter.get_nodes_from_documents(documents)
        logger.info(f"Successfully generated {len(nodes)} semantic chunks/nodes.")
        return nodes
    except Exception as e:
        logger.error(f"Error during semantic splitting: {str(e)}")
        # Return empty list on failure
        return []
