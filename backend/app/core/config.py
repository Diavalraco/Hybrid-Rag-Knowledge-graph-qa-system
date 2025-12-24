"""
Configuration management for the Hybrid RAG + KG system.
Centralizes all environment variables and settings.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_title: str = "Hybrid RAG + Knowledge Graph QA System"
    api_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # LLM Configuration (OpenAI-compatible)
    llm_api_base: str = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "1000"))
    
    # Embedding Configuration
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
    
    # Vector Store Configuration (FAISS)
    faiss_index_path: str = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # Neo4j Configuration
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # Retrieval Configuration
    top_k_vector: int = int(os.getenv("TOP_K_VECTOR", "5"))
    top_k_kg: int = int(os.getenv("TOP_K_KG", "10"))
    kg_max_depth: int = int(os.getenv("KG_MAX_DEPTH", "2"))
    
    # Hallucination Control
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.4"))  # Lowered for better testing
    min_context_length: int = int(os.getenv("MIN_CONTEXT_LENGTH", "50"))  # Lowered threshold
    
    # Data Storage
    data_dir: str = os.getenv("DATA_DIR", "./data")
    documents_dir: str = os.getenv("DOCUMENTS_DIR", "./data/documents")
    
    # CORS Configuration
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

