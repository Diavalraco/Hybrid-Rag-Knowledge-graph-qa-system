"""
Pydantic schemas for request/response models.
Ensures type safety and validation across the API.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


class DocumentIngestRequest(BaseModel):
    """Request model for document ingestion."""
    file_name: str = Field(..., description="Name of the document file")
    file_content: str = Field(..., description="Base64 encoded file content or raw text")
    file_type: str = Field(..., description="File type: 'pdf', 'txt', or 'text'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_name": "document.pdf",
                "file_content": "Base64 content here",
                "file_type": "pdf"
            }
        }


class DocumentIngestResponse(BaseModel):
    """Response model for document ingestion."""
    success: bool = Field(..., description="Whether ingestion was successful")
    document_id: str = Field(..., description="Unique identifier for the ingested document")
    chunks_created: int = Field(..., description="Number of chunks created")
    entities_extracted: int = Field(..., description="Number of entities extracted")
    relations_extracted: int = Field(..., description="Number of relations extracted")
    message: str = Field(..., description="Status message")


class SourceChunk(BaseModel):
    """Represents a retrieved document chunk."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Source document identifier")
    content: str = Field(..., description="Chunk text content")
    score: float = Field(..., description="Relevance score (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class KGEntity(BaseModel):
    """Represents a knowledge graph entity."""
    entity_id: str = Field(..., description="Entity identifier")
    entity_type: str = Field(..., description="Type/label of the entity")
    name: str = Field(..., description="Entity name")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Entity properties")


class KGRelation(BaseModel):
    """Represents a knowledge graph relation."""
    source_entity: str = Field(..., description="Source entity name")
    target_entity: str = Field(..., description="Target entity name")
    relation_type: str = Field(..., description="Type of relation")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relation properties")


class KGContext(BaseModel):
    """Context retrieved from knowledge graph."""
    entities: List[KGEntity] = Field(default_factory=list, description="Relevant entities")
    relations: List[KGRelation] = Field(default_factory=list, description="Relevant relations")
    traversal_path: List[str] = Field(default_factory=list, description="Path taken in graph traversal")


class QueryRequest(BaseModel):
    """Request model for querying the system."""
    question: str = Field(..., min_length=1, description="User's question")
    use_hybrid: bool = Field(True, description="Whether to use hybrid retrieval (vector + KG)")
    top_k: Optional[int] = Field(None, description="Override default top_k for retrieval")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the relationship between X and Y?",
                "use_hybrid": True,
                "top_k": 5
            }
        }


class QueryResponse(BaseModel):
    """Response model for query results."""
    answer: str = Field(..., description="Generated answer to the question")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    sources: List[SourceChunk] = Field(default_factory=list, description="Retrieved source chunks")
    kg_context: Optional[KGContext] = Field(None, description="Knowledge graph context used")
    query_type: str = Field(..., description="Classified query type (factual/relational/reasoning)")
    reasoning_steps: List[str] = Field(default_factory=list, description="Steps taken in retrieval")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    agent_architecture: Optional[str] = Field(None, description="Architecture type (multi-agent/single-agent)")
    rejected: Optional[bool] = Field(None, description="Whether answer was rejected")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Based on the retrieved context...",
                "confidence": 0.85,
                "sources": [],
                "kg_context": None,
                "query_type": "relational",
                "reasoning_steps": ["Retrieved 5 chunks", "Found 3 entities in KG"],
                "timestamp": "2024-01-01T12:00:00"
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    vector_store_ready: bool = Field(..., description="Whether FAISS index is ready")
    kg_store_ready: bool = Field(..., description="Whether Neo4j is connected")
    llm_service_ready: bool = Field(..., description="Whether LLM service is accessible")
    total_documents: int = Field(..., description="Total number of ingested documents")
    total_chunks: int = Field(..., description="Total number of chunks in vector store")
    total_entities: int = Field(..., description="Total number of entities in knowledge graph")

