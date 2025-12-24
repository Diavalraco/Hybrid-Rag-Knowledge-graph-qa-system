"""
Query API endpoint.
Handles user queries and returns answers using hybrid RAG.
"""
from fastapi import APIRouter, HTTPException, Request
from app.models.schemas import QueryRequest, QueryResponse
from app.core.logging import logger
from datetime import datetime


router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query(
    request_body: QueryRequest,
    http_request: Request
):
    """
    Process a user query using hybrid RAG + KG retrieval.
    
    This endpoint:
    1. Classifies the query type
    2. Retrieves relevant chunks from vector store
    3. Retrieves related entities/relations from knowledge graph
    4. Merges context and generates answer
    5. Validates answer (hallucination control)
    6. Returns answer with confidence and sources
    
    Args:
        request: Query request with question
        app_request: FastAPI Request object to access app state
        
    Returns:
        QueryResponse with answer, confidence, sources, and metadata
    """
    try:
        if not request_body.question or not request_body.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Get RAG service from app state
        rag_service = http_request.app.state.get_rag_service()
        
        logger.info(f"Processing query: {request_body.question[:100]}")
        
        # Process query using RAG service
        result = rag_service.query(
            question=request_body.question,
            use_hybrid=request_body.use_hybrid,
            top_k=request_body.top_k
        )
        
        # Convert sources to schema format
        from app.models.schemas import SourceChunk
        source_chunks = [
            SourceChunk(
                chunk_id=src.get("chunk_id", ""),
                document_id=src.get("document_id", ""),
                content=src.get("content", ""),
                score=src.get("score", 0.0),
                metadata=src.get("metadata", {})
            )
            for src in result.get("sources", [])
        ]
        
        # Convert KG context if present
        kg_context = None
        if result.get("kg_context"):
            from app.models.schemas import KGContext, KGEntity, KGRelation
            kg_data = result["kg_context"]
            kg_context = KGContext(
                entities=[
                    KGEntity(**entity) for entity in kg_data.get("entities", [])
                ],
                relations=[
                    KGRelation(**rel) for rel in kg_data.get("relations", [])
                ],
                traversal_path=kg_data.get("traversal_path", [])
            )
        
        response = QueryResponse(
            answer=result["answer"],
            confidence=result["confidence"],
            sources=source_chunks,
            kg_context=kg_context,
            query_type=result["query_type"],
            reasoning_steps=result.get("reasoning_steps", []),
            timestamp=datetime.now(),
            agent_architecture=result.get("agent_architecture"),
            rejected=result.get("rejected", False)
        )
        
        logger.info(f"Query processed successfully. Confidence: {result['confidence']:.2f}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
