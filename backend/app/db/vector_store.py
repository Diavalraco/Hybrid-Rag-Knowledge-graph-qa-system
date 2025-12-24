"""
FAISS vector store implementation for efficient similarity search.
Stores document embeddings and provides retrieval capabilities.
"""
import faiss
import numpy as np
import pickle
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from uuid import uuid4

from app.core.config import settings
from app.core.logging import logger


class VectorStore:
    """
    Manages FAISS index for vector similarity search.
    Stores document chunks with metadata for retrieval.
    """
    
    def __init__(self):
        """Initialize the vector store with FAISS index."""
        self.index: Optional[faiss.Index] = None
        self.dimension = settings.embedding_dimension
        self.metadata: List[Dict[str, Any]] = []
        self.index_path = Path(settings.faiss_index_path)
        self.metadata_path = self.index_path.parent / "metadata.json"
        
        # Create data directory if it doesn't exist
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing index if available
        self._load_index()
    
    def _load_index(self) -> None:
        """Load existing FAISS index and metadata from disk."""
        try:
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors")
                
                # Load metadata
                if self.metadata_path.exists():
                    with open(self.metadata_path, 'r') as f:
                        self.metadata = json.load(f)
                    logger.info(f"Loaded metadata for {len(self.metadata)} chunks")
            else:
                # Create new index using L2 distance (Euclidean)
                # This is appropriate for normalized embeddings
                self.index = faiss.IndexFlatL2(self.dimension)
                logger.info(f"Created new FAISS index with dimension {self.dimension}")
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            # Fallback to new index
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
    
    def _save_index(self) -> None:
        """Save FAISS index and metadata to disk."""
        try:
            if self.index is not None:
                faiss.write_index(self.index, str(self.index_path))
                with open(self.metadata_path, 'w') as f:
                    json.dump(self.metadata, f, indent=2)
                logger.debug(f"Saved index with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise
    
    def add_vectors(
        self,
        embeddings: List[List[float]],
        chunks: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Add vectors and their metadata to the index.
        
        Args:
            embeddings: List of embedding vectors
            chunks: List of chunk metadata dictionaries
            
        Returns:
            List of chunk IDs that were added
        """
        if not embeddings or not chunks:
            logger.warning("Empty embeddings or chunks provided")
            return []
        
        if len(embeddings) != len(chunks):
            raise ValueError("Number of embeddings must match number of chunks")
        
        # Convert to numpy array
        vectors = np.array(embeddings, dtype=np.float32)
        
        # Normalize vectors for cosine similarity (L2 normalization)
        # FAISS IndexFlatL2 with normalized vectors gives cosine similarity
        faiss.normalize_L2(vectors)
        
        # Generate chunk IDs if not present
        chunk_ids = []
        for i, chunk in enumerate(chunks):
            if 'chunk_id' not in chunk:
                chunk['chunk_id'] = str(uuid4())
            chunk_ids.append(chunk['chunk_id'])
            chunk['index_position'] = len(self.metadata) + i
        
        # Add to metadata
        self.metadata.extend(chunks)
        
        # Add vectors to index
        self.index.add(vectors)
        
        # Save index after addition
        self._save_index()
        
        logger.info(f"Added {len(embeddings)} vectors to index. Total: {self.index.ntotal}")
        return chunk_ids
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for similar vectors in the index.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return (defaults to config setting)
            
        Returns:
            List of tuples (chunk_metadata, distance_score)
            Lower distance = higher similarity
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty, returning no results")
            return []
        
        if top_k is None:
            top_k = settings.top_k_vector
        
        # Convert query to numpy array and normalize
        query_vector = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_vector)
        
        # Search in FAISS (returns distances and indices)
        distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
        
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0:  # Invalid index
                continue
            
            # Convert distance to similarity score (1 - normalized distance)
            # Since we're using L2 on normalized vectors, distance ranges from 0 to 2
            similarity_score = 1.0 - (distance / 2.0)
            similarity_score = max(0.0, min(1.0, similarity_score))  # Clamp to [0, 1]
            
            # Get metadata
            if idx < len(self.metadata):
                chunk_metadata = self.metadata[idx].copy()
                chunk_metadata['similarity_score'] = similarity_score
                results.append((chunk_metadata, similarity_score))
        
        logger.debug(f"Retrieved {len(results)} results for query")
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "index_type": type(self.index).__name__ if self.index else None,
            "metadata_count": len(self.metadata)
        }
    
    def delete_by_document_id(self, document_id: str) -> int:
        """
        Delete all chunks associated with a document.
        Note: FAISS doesn't support deletion, so we mark chunks as deleted in metadata.
        For production, consider rebuilding index or using a more advanced FAISS structure.
        
        Args:
            document_id: ID of document to remove
            
        Returns:
            Number of chunks marked for deletion
        """
        deleted_count = 0
        for metadata in self.metadata:
            if metadata.get('document_id') == document_id:
                metadata['deleted'] = True
                deleted_count += 1
        
        if deleted_count > 0:
            self._save_index()
            logger.info(f"Marked {deleted_count} chunks for deletion from document {document_id}")
        
        return deleted_count

