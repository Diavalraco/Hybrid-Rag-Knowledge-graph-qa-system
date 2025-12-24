"""
Health check API endpoint.
Provides system status and statistics.
"""
from fastapi import APIRouter, HTTPException, Request
from app.models.schemas import HealthResponse
from app.core.logging import logger


router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check(http_request: Request):
    """
    Check system health and return statistics.
    
    Args:
        app_request: FastAPI Request object to access app state
        
    Returns:
        HealthResponse with system status and statistics
    """
    try:
        # Get services from app state
        vector_store = http_request.app.state.get_vector_store()
        neo4j_client = http_request.app.state.get_neo4j_client()
        llm_service = http_request.app.state.get_llm_service()
        
        # Check vector store
        vector_store_ready = vector_store.index is not None
        vector_stats = vector_store.get_stats()
        
        # Check Neo4j
        kg_store_ready = False
        kg_stats = {"total_nodes": 0, "total_relationships": 0}
        if neo4j_client:
            try:
                kg_stats = neo4j_client.get_stats()
                kg_store_ready = neo4j_client.driver is not None
            except Exception as e:
                logger.warning(f"Neo4j health check failed: {e}")
        
        # Check LLM service (simple connection test)
        llm_service_ready = False
        try:
            # Try a minimal API call (or just check if credentials are set)
            if llm_service.api_key:
                llm_service_ready = True
        except Exception as e:
            logger.warning(f"LLM service health check failed: {e}")
        
        # Determine overall status
        status = "healthy" if (vector_store_ready and kg_store_ready and llm_service_ready) else "degraded"
        
        return HealthResponse(
            status=status,
            vector_store_ready=vector_store_ready,
            kg_store_ready=kg_store_ready,
            llm_service_ready=llm_service_ready,
            total_documents=0,  # TODO: Track document count separately
            total_chunks=vector_stats.get("total_vectors", 0),
            total_entities=kg_stats.get("total_nodes", 0)
        )
    
    except Exception as e:
        logger.error(f"Error in health check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
