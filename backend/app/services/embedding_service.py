"""
Embedding service for generating vector representations of text.
Uses OpenAI-compatible API for embeddings.
"""
import httpx
from typing import List
from app.core.config import settings
from app.core.logging import logger


class EmbeddingService:
    """
    Service for generating text embeddings.
    Abstracts the embedding API calls for easy replacement.
    """
    
    def __init__(self):
        """Initialize embedding service with API configuration."""
        self.api_base = settings.llm_api_base
        self.api_key = settings.llm_api_key
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (lists of floats)
        """
        if not texts:
            return []
        
        # Batch process embeddings (OpenAI supports up to 2048 texts per request)
        all_embeddings = []
        batch_size = 100  # Conservative batch size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                embeddings = self._get_embeddings_batch(batch)
                all_embeddings.extend(embeddings)
            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i}: {e}")
                # Fill with zero vectors as fallback (not ideal, but prevents crashes)
                all_embeddings.extend([[0.0] * self.dimension] * len(batch))
        
        logger.debug(f"Generated {len(all_embeddings)} embeddings")
        return all_embeddings
    
    def _get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts using OpenAI-compatible API.
        
        Args:
            texts: Batch of text strings
            
        Returns:
            List of embedding vectors
        """
        url = f"{self.api_base}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "input": texts
        }
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Extract embeddings from response
            embeddings = [item['embedding'] for item in result['data']]
            return embeddings
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector
        """
        embeddings = self.get_embeddings([text])
        return embeddings[0] if embeddings else [0.0] * self.dimension

