import os
import logging
from app.core.config import settings

logger = logging.getLogger("askdocs-rag.services.observability")

def setup_observability():
    """
    Sets up open-source Arize Phoenix tracing and OpenTelemetry instrumentation
    globally for LlamaIndex.
    """
    enable_tracing = os.getenv("PHOENIX_ENABLE", "true").lower() == "true"
    
    if not enable_tracing:
        logger.info("Arize Phoenix observability tracing is disabled.")
        return

    try:
        logger.info("Initializing Arize Phoenix instrumentation...")
        
        # Launch Phoenix collector server locally in the background
        # Phoenix UI runs at http://localhost:6006 by default
        import phoenix as px
        from phoenix.otel import register
        from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

        # Starts the collector session in background
        px.launch_app()
        logger.info("Phoenix collector server successfully launched. Dashboard available at http://localhost:6006")
        
        # Register tracer provider with Phoenix collector
        tracer_provider = register()
        
        # Instrument LlamaIndex globally
        LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
        logger.info("LlamaIndex globally instrumented for OpenTelemetry tracing.")
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry/Phoenix tracing: {str(e)}")
        logger.warning("Continuing execution without tracing observability.")
