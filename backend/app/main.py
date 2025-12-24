"""
Main FastAPI application.
Initializes services and mounts API routes.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import logger
from app.api import ingest, query, health

# Initialize services (singleton pattern)
vector_store = None
neo4j_client = None
embedding_service = None
llm_service = None
kg_service = None
hallucination_guard = None
rag_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.
    Initializes services on startup and cleans up on shutdown.
    """
    global vector_store, neo4j_client, embedding_service, llm_service
    global kg_service, hallucination_guard, rag_service
    
    # Startup
    logger.info("Starting Hybrid RAG + KG system...")
    
    try:
        # Initialize database clients
        from app.db.vector_store import VectorStore
        from app.db.neo4j_client import Neo4jClient
        
        vector_store = VectorStore()
        try:
            neo4j_client = Neo4jClient()
        except Exception as e:
            logger.warning(f"Neo4j initialization failed: {e}. Running in vector-only mode.")
            neo4j_client = None
        
        # Initialize services
        from app.services.embedding_service import EmbeddingService
        from app.services.llm_service import LLMService
        from app.services.kg_service import KGService
        from app.services.hallucination_guard import HallucinationGuard
        from app.services.rag_service import RAGService
        
        embedding_service = EmbeddingService()
        llm_service = LLMService()
        # Only create KG service if Neo4j is available
        if neo4j_client and neo4j_client.driver:
            kg_service = KGService(neo4j_client)
        else:
            logger.warning("KG service disabled - Neo4j not available")
            kg_service = None
        hallucination_guard = HallucinationGuard()
        rag_service = RAGService(
            vector_store=vector_store,
            embedding_service=embedding_service,
            llm_service=llm_service,
            kg_service=kg_service,
            hallucination_guard=hallucination_guard
        )
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing services: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if neo4j_client:
        neo4j_client.close()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan
)

# Add CORS middleware
# Allow all origins in production (Render/Vercel), or specific frontend URLs
cors_origins = settings.cors_origins
# In production (Render/Vercel), allow all origins if "*" is in the list
if "*" in cors_origins or os.getenv("RENDER") or os.getenv("VERCEL"):
    # Allow all origins in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Must be False when allow_origins=["*"]
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # In development, use specific origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Dependency injection functions
def get_vector_store():
    """Get vector store instance."""
    return vector_store


def get_neo4j_client():
    """Get Neo4j client instance."""
    return neo4j_client


def get_embedding_service():
    """Get embedding service instance."""
    return embedding_service


def get_llm_service():
    """Get LLM service instance."""
    return llm_service


def get_kg_service():
    """Get KG service instance."""
    return kg_service


def get_rag_service():
    """Get RAG service instance."""
    return rag_service


# Store dependency functions in app state for use in routers
app.state.get_vector_store = get_vector_store
app.state.get_neo4j_client = get_neo4j_client
app.state.get_embedding_service = get_embedding_service
app.state.get_llm_service = get_llm_service
app.state.get_kg_service = get_kg_service
app.state.get_rag_service = get_rag_service

# Include routers
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(health.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Hybrid RAG + Knowledge Graph Question Answering System",
        "version": settings.api_version,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )

