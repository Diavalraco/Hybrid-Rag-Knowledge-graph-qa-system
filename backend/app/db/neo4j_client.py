"""
Neo4j client for knowledge graph operations.
Manages entities, relationships, and graph traversal queries.
"""
from typing import List, Dict, Any, Optional, Tuple
from neo4j import GraphDatabase
from app.core.config import settings
from app.core.logging import logger


class Neo4jClient:
    """
    Client for interacting with Neo4j knowledge graph.
    Handles entity and relationship storage, retrieval, and traversal.
    """
    
    def __init__(self):
        """Initialize Neo4j driver connection."""
        self.driver = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Connected to Neo4j successfully")
        except Exception as e:
            logger.warning(f"Failed to connect to Neo4j: {e}")
            logger.warning("System will continue without Knowledge Graph functionality. Install and start Neo4j to enable KG features.")
            # Don't raise - allow system to start without Neo4j (vector-only mode)
    
    def close(self) -> None:
        """Close Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def add_entities(
        self,
        entities: List[Dict[str, Any]]
    ) -> int:
        """
        Add entities to the knowledge graph.
        Creates nodes with labels and properties.
        
        Args:
            entities: List of entity dicts with 'name', 'type', and optional 'properties'
            
        Returns:
            Number of entities added
        """
        if not entities:
            return 0
        
        added_count = 0
        with self.driver.session() as session:
            for entity in entities:
                try:
                    entity_name = entity.get('name', '').strip()
                    entity_type = entity.get('type', 'Entity').strip()
                    properties = entity.get('properties', {})
                    
                    if not entity_name:
                        continue
                    
                    # Merge node (creates if not exists, updates if exists)
                    # Using MERGE prevents duplicates based on name and type
                    query = f"""
                    MERGE (e:{entity_type} {{name: $name}})
                    SET e += $properties
                    SET e.updated_at = timestamp()
                    RETURN e
                    """
                    
                    result = session.run(
                        query,
                        name=entity_name,
                        properties=properties
                    )
                    result.single()  # Execute query
                    added_count += 1
                except Exception as e:
                    logger.warning(f"Error adding entity {entity.get('name')}: {e}")
                    continue
        
        logger.info(f"Added {added_count} entities to knowledge graph")
        return added_count
    
    def add_relations(
        self,
        relations: List[Dict[str, Any]]
    ) -> int:
        """
        Add relationships between entities.
        
        Args:
            relations: List of relation dicts with 'source', 'target', 'type', and optional 'properties'
            
        Returns:
            Number of relations added
        """
        if not relations:
            return 0
        
        added_count = 0
        with self.driver.session() as session:
            for relation in relations:
                try:
                    source = relation.get('source', '').strip()
                    target = relation.get('target', '').strip()
                    rel_type = relation.get('type', 'RELATED_TO').strip()
                    properties = relation.get('properties', {})
                    
                    if not source or not target:
                        continue
                    
                    # Create relationship between entities (creates nodes if they don't exist)
                    # Using MERGE ensures we don't create duplicate relationships
                    query = """
                    MATCH (s {name: $source})
                    MATCH (t {name: $target})
                    MERGE (s)-[r:%s {created_at: timestamp()}]->(t)
                    SET r += $properties
                    RETURN r
                    """ % rel_type
                    
                    result = session.run(
                        query,
                        source=source,
                        target=target,
                        properties=properties
                    )
                    result.single()  # Execute query
                    added_count += 1
                except Exception as e:
                    logger.warning(f"Error adding relation {source}-{rel_type}->{target}: {e}")
                    continue
        
        logger.info(f"Added {added_count} relations to knowledge graph")
        return added_count
    
    def extract_entities_from_text(
        self,
        text: str
    ) -> List[str]:
        """
        Extract entity names mentioned in text.
        Simple implementation - matches entities by name in the graph.
        
        Args:
            text: Input text to extract entities from
            
        Returns:
            List of entity names found in the graph
        """
        # This is a simplified version - in production, use NER models
        # Here we'll query for entities that appear as words in the text
        words = text.lower().split()
        entities = []
        
        with self.driver.session() as session:
            # Find entities whose names appear in the text
            query = """
            MATCH (e)
            WHERE toLower(e.name) IN $words
            RETURN DISTINCT e.name AS name
            LIMIT 50
            """
            
            result = session.run(query, words=words)
            for record in result:
                entities.append(record['name'])
        
        return entities
    
    def get_related_entities(
        self,
        entity_names: List[str],
        max_depth: int = None,
        max_results: int = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Get entities and relations connected to the given entities.
        Performs graph traversal up to max_depth.
        
        Args:
            entity_names: List of entity names to start traversal from
            max_depth: Maximum traversal depth (defaults to config)
            max_results: Maximum number of results to return
            
        Returns:
            Tuple of (entities_list, relations_list)
        """
        if not entity_names:
            return [], []
        
        if max_depth is None:
            max_depth = settings.kg_max_depth
        
        if max_results is None:
            max_results = settings.top_k_kg
        
        entities = []
        relations = []
        
        with self.driver.session() as session:
            # Traverse graph from starting entities
            # This query finds all nodes and relationships within max_depth
            query = """
            MATCH path = (start {name: $entity_name})-[*1..%d]-(connected)
            WHERE ALL(name IN $entity_names WHERE name <> connected.name)
            WITH path, connected, relationships(path) AS rels
            LIMIT $max_results
            RETURN DISTINCT connected AS entity, rels AS relations
            """ % max_depth
            
            seen_entities = set()
            seen_relations = set()
            
            for entity_name in entity_names[:5]:  # Limit starting points
                try:
                    result = session.run(
                        query,
                        entity_name=entity_name,
                        entity_names=entity_names,
                        max_results=max_results
                    )
                    
                    for record in result:
                        # Extract entity
                        entity = record['entity']
                        entity_name_key = entity.get('name')
                        
                        if entity_name_key and entity_name_key not in seen_entities:
                            seen_entities.add(entity_name_key)
                            entities.append({
                                'entity_id': str(entity.id),
                                'entity_type': list(entity.labels)[0] if entity.labels else 'Entity',
                                'name': entity_name_key,
                                'properties': dict(entity)
                            })
                        
                        # Extract relations
                        for rel in record['relations']:
                            rel_key = f"{rel.start_node['name']}-{rel.type}->{rel.end_node['name']}"
                            if rel_key not in seen_relations:
                                seen_relations.add(rel_key)
                                relations.append({
                                    'source_entity': rel.start_node['name'],
                                    'target_entity': rel.end_node['name'],
                                    'relation_type': rel.type,
                                    'properties': dict(rel)
                                })
                        
                        if len(entities) >= max_results:
                            break
                except Exception as e:
                    logger.warning(f"Error traversing from entity {entity_name}: {e}")
                    continue
        
        logger.debug(f"Retrieved {len(entities)} entities and {len(relations)} relations")
        return entities[:max_results], relations[:max_results]
    
    def get_entity_path(
        self,
        source_entity: str,
        target_entity: str,
        max_depth: int = 3
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Find shortest path between two entities.
        
        Args:
            source_entity: Name of source entity
            target_entity: Name of target entity
            max_depth: Maximum path length
            
        Returns:
            List of nodes in the path, or None if no path found
        """
        with self.driver.session() as session:
            query = """
            MATCH path = shortestPath(
                (s {name: $source})-[*..%d]-(t {name: $target})
            )
            RETURN path
            """ % max_depth
            
            result = session.run(query, source=source_entity, target=target_entity)
            record = result.single()
            
            if record:
                path = record['path']
                nodes = [{'name': node['name'], 'type': list(node.labels)[0]} for node in path.nodes]
                return nodes
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph."""
        try:
            with self.driver.session() as session:
                # Count nodes
                node_result = session.run("MATCH (n) RETURN count(n) AS count")
                node_count = node_result.single()['count']
                
                # Count relationships
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
                rel_count = rel_result.single()['count']
                
                # Count node types
                type_result = session.run("""
                    MATCH (n)
                    RETURN labels(n)[0] AS type, count(n) AS count
                    ORDER BY count DESC
                """)
                node_types = {record['type']: record['count'] for record in type_result}
                
                return {
                    "total_nodes": node_count,
                    "total_relationships": rel_count,
                    "node_types": node_types
                }
        except Exception as e:
            logger.error(f"Error getting KG stats: {e}")
            return {
                "total_nodes": 0,
                "total_relationships": 0,
                "node_types": {}
            }
    
    def clear_all(self) -> None:
        """Clear all data from the knowledge graph. Use with caution!"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.warning("Cleared all data from knowledge graph")

