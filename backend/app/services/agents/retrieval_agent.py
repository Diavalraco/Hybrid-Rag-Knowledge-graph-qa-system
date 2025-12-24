"""
Retrieval Agent - Specialized in finding and merging relevant context.
Handles both vector search and knowledge graph traversal.
"""
from typing import List, Dict, Any, Tuple
from app.db.vector_store import VectorStore
from app.services.embedding_service import EmbeddingService
from app.services.kg_service import KGService
from app.utils.entity_extraction import extract_entities_from_query
from app.core.config import settings
from app.core.logging import logger


class RetrievalAgent:
    """
    Agent responsible for retrieving relevant context from both
    vector store and knowledge graph based on query type.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        kg_service: KGService = None
    ):
        """
        Initialize Retrieval Agent.
        
        Args:
            vector_store: FAISS vector store instance
            embedding_service: Embedding service for query encoding
            kg_service: Knowledge graph service (optional)
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.kg_service = kg_service
    
    def retrieve_context(
        self,
        question: str,
        query_type: str,
        use_hybrid: bool = True,
        top_k: int = None
    ) -> Dict[str, Any]:
        """
        Retrieve context from vector store and knowledge graph.
        Agent decides on retrieval strategy based on query type.
        
        Args:
            question: User question
            query_type: Type of query (factual/relational/reasoning)
            use_hybrid: Whether to use both vector and KG
            top_k: Number of results to retrieve
            
        Returns:
            Dictionary with:
            - vector_results: List of (chunk_metadata, score) tuples
            - kg_entities: List of KG entities
            - kg_relations: List of KG relations
            - kg_traversal_path: Path taken in graph
            - reasoning: Agent's reasoning steps
        """
        reasoning_steps = []
        
        # Step 1: Vector retrieval (always performed)
        query_embedding = self.embedding_service.get_embedding(question)
        vector_results = self.vector_store.search(
            query_embedding,
            top_k=top_k or settings.top_k_vector
        )
        reasoning_steps.append(f"Retrieved {len(vector_results)} chunks from vector store")
        
        # Step 2: Knowledge graph retrieval (if hybrid and KG available)
        kg_entities = []
        kg_relations = []
        kg_traversal_path = []
        
        if use_hybrid and self.kg_service and query_type in ["relational", "reasoning"]:
            # Agent prioritizes KG for relational/reasoning queries
            try:
                kg_entities, kg_relations, kg_traversal_path = self.kg_service.retrieve_context_for_query(
                    question,
                    max_depth=settings.kg_max_depth,
                    max_results=settings.top_k_kg
                )
                reasoning_steps.append(
                    f"Retrieved {len(kg_entities)} entities and {len(kg_relations)} relations from KG"
                )
                reasoning_steps.extend(kg_traversal_path[:3])
            except Exception as e:
                logger.warning(f"KG retrieval failed: {e}")
                reasoning_steps.append("KG retrieval unavailable - using vector search only")
        elif use_hybrid and not self.kg_service:
            reasoning_steps.append("KG service unavailable - using vector search only")
        elif query_type == "factual":
            reasoning_steps.append("Factual query - prioritizing vector search over KG")
        
        # Step 3: Agent decides on retrieval strategy based on query type
        # For factual queries, emphasize vector results
        # For relational queries, emphasize KG results
        # For reasoning queries, use balanced approach
        
        return {
            "vector_results": vector_results,
            "kg_entities": kg_entities,
            "kg_relations": kg_relations,
            "kg_traversal_path": kg_traversal_path,
            "reasoning": reasoning_steps,
            "query_type": query_type
        }
    
    def merge_context(
        self,
        vector_results: List[Tuple[Dict[str, Any], float]],
        kg_entities: List[Dict[str, Any]],
        kg_relations: List[Dict[str, Any]],
        query_type: str
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Merge vector and KG context intelligently based on query type.
        Agent decides on merging strategy.
        
        Args:
            vector_results: Results from vector search
            kg_entities: Entities from knowledge graph
            kg_relations: Relations from knowledge graph
            query_type: Type of query (factual/relational/reasoning)
            
        Returns:
            Tuple of (merged_context_string, sources_list)
        """
        sources = []
        context_parts = []
        
        # Agent strategy: Add vector chunks (always include these)
        for chunk_metadata, score in vector_results:
            if chunk_metadata.get('deleted', False):
                continue
            
            sources.append({
                "chunk_id": chunk_metadata.get("chunk_id", ""),
                "document_id": chunk_metadata.get("document_id", ""),
                "content": chunk_metadata.get("content", ""),
                "score": score,  # This is the similarity score from FAISS
                "similarity_score": score,  # Also store as similarity_score for compatibility
                "metadata": {
                    k: v for k, v in chunk_metadata.items()
                    if k not in ['chunk_id', 'document_id', 'content', 'similarity_score']
                }
            })
            context_parts.append(
                f"[Vector Chunk {len(context_parts) + 1}]\n{chunk_metadata.get('content', '')}"
            )
        
        # Agent strategy: Add KG context based on query type
        if query_type == "relational" and kg_relations:
            # For relational queries, prioritize KG relations
            kg_context = "Knowledge Graph Relations:\n"
            for rel in kg_relations[:15]:  # More relations for relational queries
                kg_context += f"- {rel['source_entity']} --[{rel['relation_type']}]--> {rel['target_entity']}\n"
            context_parts.insert(0, kg_context)  # Put KG first for relational queries
        
        if query_type in ["relational", "reasoning"] and kg_entities:
            # Add entities for relational/reasoning queries
            entity_context = "Related Entities:\n"
            for entity in kg_entities[:10]:
                entity_type = entity.get('entity_type', 'Entity')
                entity_context += f"- {entity['name']} (Type: {entity_type})\n"
            context_parts.append(entity_context)
        
        merged_context = "\n\n---\n\n".join(context_parts)
        return merged_context, sources

