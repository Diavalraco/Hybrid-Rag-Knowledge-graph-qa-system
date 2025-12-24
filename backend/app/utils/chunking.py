"""
Document chunking utilities.
Splits documents into overlapping chunks for better retrieval coverage.
"""
import re
from typing import List, Dict, Any
from app.core.config import settings
from app.core.logging import logger


def chunk_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None
) -> List[str]:
    """
    Split text into overlapping chunks.
    Uses sentence boundaries when possible for better coherence.
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum characters per chunk (defaults to config)
        chunk_overlap: Number of characters to overlap between chunks (defaults to config)
        
    Returns:
        List of text chunks
    """
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if chunk_overlap is None:
        chunk_overlap = settings.chunk_overlap
    
    # Clean and normalize text
    text = text.strip()
    if not text:
        return []
    
    # Split by sentences (simple approach using punctuation)
    # This preserves semantic coherence better than arbitrary character splits
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # If adding this sentence would exceed chunk size
        if current_chunk and len(current_chunk) + len(sentence) + 1 > chunk_size:
            # Save current chunk
            chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap from previous chunk
            # Take last chunk_overlap characters from previous chunk
            overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else current_chunk
            current_chunk = overlap_text + " " + sentence
        else:
            # Add sentence to current chunk
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
    
    # Add final chunk if it exists
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # Fallback: if no chunks created (e.g., very long single sentence), split by character
    if not chunks:
        for i in range(0, len(text), chunk_size - chunk_overlap):
            chunk = text[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk.strip())
    
    logger.debug(f"Created {len(chunks)} chunks from text of length {len(text)}")
    return chunks


def chunk_document(
    document_id: str,
    text: str,
    metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Chunk a document and return chunks with metadata.
    
    Args:
        document_id: Unique identifier for the document
        text: Document text content
        metadata: Additional metadata to attach to chunks
        
    Returns:
        List of chunk dictionaries with content and metadata
    """
    chunks = chunk_text(text)
    
    chunk_objects = []
    for i, chunk_content in enumerate(chunks):
        chunk_obj = {
            "document_id": document_id,
            "chunk_index": i,
            "content": chunk_content,
            "chunk_length": len(chunk_content),
            "total_chunks": len(chunks)
        }
        
        # Add provided metadata
        if metadata:
            chunk_obj.update(metadata)
        
        chunk_objects.append(chunk_obj)
    
    logger.info(f"Created {len(chunk_objects)} chunks for document {document_id}")
    return chunk_objects

