"""
Hybrid RAG service combining vector search and knowledge graph.
Orchestrates the retrieval and answer generation pipeline using multi-agent system.
"""
from typing import List, Dict, Any, Tuple, Optional
from app.db.vector_store import VectorStore
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.kg_service import KGService
from app.services.hallucination_guard import HallucinationGuard
from app.services.agents.retrieval_agent import RetrievalAgent
from app.services.agents.generation_agent import GenerationAgent
from app.core.config import settings
from app.core.logging import logger


class RAGService:
    """
    Hybrid RAG service using multi-agent architecture:
    - Retrieval Agent: Handles vector search and KG traversal
    - Generation Agent: Handles answer generation and validation
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        llm_service: LLMService,
        kg_service: KGService,
        hallucination_guard: HallucinationGuard
    ):
        """
        Initialize RAG service with multi-agent system.
        
        Args:
            vector_store: FAISS vector store instance
            embedding_service: Embedding service instance
            llm_service: LLM service instance
            kg_service: Knowledge graph service instance
            hallucination_guard: Hallucination guard instance
        """
        # Initialize agents
        self.retrieval_agent = RetrievalAgent(
            vector_store=vector_store,
            embedding_service=embedding_service,
            kg_service=kg_service
        )
        
        self.generation_agent = GenerationAgent(
            llm_service=llm_service,
            hallucination_guard=hallucination_guard
        )
        
        # Keep references for backward compatibility
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.kg_service = kg_service
        self.hallucination_guard = hallucination_guard
    
    def query(
        self,
        question: str,
        use_hybrid: bool = True,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process a user query using hybrid retrieval.
        
        This is the core pipeline:
        1. Classify query type
        2. Retrieve from vector store
        3. Retrieve from knowledge graph (if hybrid)
        4. Merge and rank context
        5. Generate answer
        6. Validate answer (hallucination control)
        
        Args:
            question: User question
            use_hybrid: Whether to use both vector and KG retrieval
            top_k: Override default top_k for retrieval
            
        Returns:
            Dictionary with answer, confidence, sources, and metadata
        """
        # Multi-agent pipeline
        
        # Agent 1: Generation Agent classifies the query
        query_type = self.generation_agent.classify_query(question)
        reasoning_steps = [f"Query classified as: {query_type}"]
        
        # Agent 2: Retrieval Agent finds relevant context
        retrieval_result = self.retrieval_agent.retrieve_context(
            question=question,
            query_type=query_type,
            use_hybrid=use_hybrid,
            top_k=top_k
        )
        reasoning_steps.extend(retrieval_result["reasoning"])
        
        # Agent 2: Retrieval Agent merges context intelligently
        merged_context, sources = self.retrieval_agent.merge_context(
            retrieval_result["vector_results"],
            retrieval_result["kg_entities"],
            retrieval_result["kg_relations"],
            query_type
        )
        reasoning_steps.append(f"Merged context length: {len(merged_context)} characters")
        
        # Agent 1: Generation Agent generates and validates answer
        generation_result = self.generation_agent.generate_answer(
            question=question,
            context=merged_context,
            sources=sources,
            query_type=query_type
        )
        reasoning_steps.extend(generation_result["reasoning"])
        
        # Extract results
        answer = generation_result["answer"]
        confidence = generation_result["confidence"]
        validation = generation_result["validation"]
        
        # Prepare KG context for response
        kg_context = None
        if retrieval_result["kg_entities"] or retrieval_result["kg_relations"]:
            from app.models.schemas import KGContext, KGEntity, KGRelation
            kg_context = KGContext(
                entities=[
                    KGEntity(
                        entity_id=e.get("entity_id", ""),
                        entity_type=e.get("entity_type", "Entity"),
                        name=e.get("name", ""),
                        properties=e.get("properties", {})
                    )
                    for e in retrieval_result["kg_entities"]
                ],
                relations=[
                    KGRelation(
                        source_entity=r.get("source_entity", ""),
                        target_entity=r.get("target_entity", ""),
                        relation_type=r.get("relation_type", "RELATED_TO"),
                        properties=r.get("properties", {})
                    )
                    for r in retrieval_result["kg_relations"]
                ],
                traversal_path=retrieval_result["kg_traversal_path"]
            )
        
        return {
            "answer": answer,
            "confidence": confidence,
            "sources": sources,
            "kg_context": kg_context.dict() if kg_context else None,
            "query_type": query_type,
            "reasoning_steps": reasoning_steps,
            "rejected": generation_result["rejected"],
            "agent_architecture": "multi-agent"  # Indicate multi-agent system
        }
    
    def _merge_context(
        self,
        vector_results: List[Tuple[Dict[str, Any], float]],
        kg_entities: List[Dict[str, Any]],
        kg_relations: List[Dict[str, Any]],
        query_type: str
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Merge vector and KG context, ranking by relevance.
        
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
        
        # Add vector chunks (already ranked by similarity)
        for chunk_metadata, score in vector_results:
            # Skip deleted chunks
            if chunk_metadata.get('deleted', False):
                continue
            
            sources.append({
                "chunk_id": chunk_metadata.get("chunk_id", ""),
                "document_id": chunk_metadata.get("document_id", ""),
                "content": chunk_metadata.get("content", ""),
                "score": score,
                "metadata": {k: v for k, v in chunk_metadata.items() if k not in ['chunk_id', 'document_id', 'content', 'similarity_score']}
            })
            context_parts.append(f"[Vector Chunk {len(context_parts) + 1}]\n{chunk_metadata.get('content', '')}")
        
        # Add KG context (especially important for relational queries)
        if query_type == "relational" and kg_relations:
            kg_context = "Knowledge Graph Relations:\n"
            for rel in kg_relations[:10]:  # Limit to top relations
                kg_context += f"- {rel['source_entity']} --[{rel['relation_type']}]--> {rel['target_entity']}\n"
            context_parts.append(kg_context)
        
        if kg_entities and query_type != "factual":
            # Add entity information for relational/reasoning queries
            entity_context = "Related Entities:\n"
            for entity in kg_entities[:10]:
                entity_context += f"- {entity['name']} (Type: {entity.get('entity_type', 'Entity')})\n"
            context_parts.append(entity_context)
        
        merged_context = "\n\n---\n\n".join(context_parts)
        return merged_context, sources

