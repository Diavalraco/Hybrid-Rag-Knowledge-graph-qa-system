"""
Knowledge Graph service for entity and relation management.
Orchestrates KG operations and provides retrieval capabilities.
"""
from typing import List, Dict, Any, Tuple, Optional
from app.db.neo4j_client import Neo4jClient
from app.utils.entity_extraction import extract_entities_from_query
from app.core.logging import logger


class KGService:
    """
    Service for knowledge graph operations.
    Handles entity/relation storage and graph-based retrieval.
    """
    
    def __init__(self, neo4j_client: Neo4jClient = None):
        """
        Initialize KG service with Neo4j client.
        
        Args:
            neo4j_client: Neo4j client instance (optional)
        """
        self.neo4j = neo4j_client
    
    def store_document_entities(
        self,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Store extracted entities and relations in knowledge graph.
        
        Args:
            entities: List of entity dictionaries
            relations: List of relation dictionaries
            
        Returns:
            Dictionary with counts of stored entities and relations
        """
        if not self.neo4j or not self.neo4j.driver:
            return {"entities_stored": 0, "relations_stored": 0}
        
        entity_count = self.neo4j.add_entities(entities)
        relation_count = self.neo4j.add_relations(relations)
        
        logger.info(f"Stored {entity_count} entities and {relation_count} relations in KG")
        
        return {
            "entities_stored": entity_count,
            "relations_stored": relation_count
        }
    
    def retrieve_context_for_query(
        self,
        query: str,
        max_depth: int = None,
        max_results: int = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
        """
        Retrieve relevant context from knowledge graph for a query.
        
        Args:
            query: User query text
            max_depth: Maximum graph traversal depth
            max_results: Maximum number of results
            
        Returns:
            Tuple of (entities_list, relations_list, traversal_path)
        """
        if not self.neo4j or not self.neo4j.driver:
            return [], [], []
        
        # Extract entities from query
        entity_names = extract_entities_from_query(query)
        
        if not entity_names:
            logger.debug("No entities found in query for KG retrieval")
            return [], [], []
        
        # Also try to match entities from the graph that appear in query text
        graph_entities = self.neo4j.extract_entities_from_text(query)
        entity_names.extend(graph_entities)
        entity_names = list(set(entity_names))  # Remove duplicates
        
        # Retrieve related entities and relations
        entities, relations = self.neo4j.get_related_entities(
            entity_names,
            max_depth=max_depth,
            max_results=max_results
        )
        
        # Build traversal path for explainability
        traversal_path = self._build_traversal_path(entity_names, entities, relations)
        
        logger.debug(f"Retrieved {len(entities)} entities and {len(relations)} relations from KG")
        return entities, relations, traversal_path
    
    def _build_traversal_path(
        self,
        starting_entities: List[str],
        retrieved_entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Build a human-readable traversal path for explainability.
        
        Args:
            starting_entities: Entities that started the traversal
            retrieved_entities: Entities retrieved from graph
            relations: Relations retrieved from graph
            
        Returns:
            List of path descriptions
        """
        path = [f"Started from entities: {', '.join(starting_entities[:5])}"]
        
        if relations:
            path.append(f"Found {len(relations)} relations")
            # Add first few relations as examples
            for rel in relations[:3]:
                path.append(f"  - {rel['source_entity']} --[{rel['relation_type']}]--> {rel['target_entity']}")
        
        if retrieved_entities:
            path.append(f"Retrieved {len(retrieved_entities)} connected entities")
        
        return path
    
    def find_entity_path(
        self,
        source_entity: str,
        target_entity: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Find path between two entities.
        Useful for relational queries.
        
        Args:
            source_entity: Source entity name
            target_entity: Target entity name
            
        Returns:
            List of nodes in path, or None if no path found
        """
        return self.neo4j.get_entity_path(source_entity, target_entity)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        return self.neo4j.get_stats()

