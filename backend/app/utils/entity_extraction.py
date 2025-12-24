"""
Entity and relation extraction utilities.
Extracts structured information from text for knowledge graph construction.
"""
import re
from typing import List, Dict, Any, Tuple
from app.core.logging import logger


def extract_entities_and_relations(
    text: str,
    use_llm: bool = False
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extract entities and relations from text.
    
    This is a simplified extraction using pattern matching.
    For production, use NER models (spaCy, transformers) or LLM-based extraction.
    
    Args:
        text: Input text to extract from
        use_llm: Whether to use LLM for extraction (not implemented in basic version)
        
    Returns:
        Tuple of (entities_list, relations_list)
    """
    entities = []
    relations = []
    
    # Simple pattern-based extraction (rule-based)
    # In production, replace with proper NER and relation extraction models
    
    # Extract capitalized phrases as potential entities (PERSON, ORG, LOCATION patterns)
    entity_patterns = [
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Multi-word capitalized entities
    ]
    
    seen_entities = set()
    potential_entities = []
    
    for pattern in entity_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            entity_name = match.group().strip()
            # Filter out common words and short entities
            if len(entity_name) > 2 and entity_name not in seen_entities:
                # Simple heuristic: if it appears multiple times, likely an entity
                count = text.count(entity_name)
                if count >= 2:  # Threshold for entity confidence
                    seen_entities.add(entity_name)
                    potential_entities.append({
                        'name': entity_name,
                        'type': _classify_entity_type(entity_name),
                        'properties': {
                            'mention_count': count,
                            'first_mention': text.find(entity_name)
                        }
                    })
    
    entities = potential_entities[:50]  # Limit entities
    
    # Extract relations using pattern matching
    # Look for relation keywords between entities
    relation_patterns = [
        (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b)\s+(is|was|are|were)\s+(a|an|the)?\s*(\w+)', 'IS_A'),
        (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b)\s+(works?|worked|working)\s+(at|for)\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b)', 'WORKS_AT'),
        (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b)\s+(located|in|at)\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b)', 'LOCATED_IN'),
    ]
    
    seen_relations = set()
    for pattern, rel_type in relation_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            groups = match.groups()
            if len(groups) >= 2:
                source = groups[0].strip()
                target = groups[-1].strip() if groups[-1] else None
                
                if source and target and source in seen_entities and target in seen_entities:
                    rel_key = f"{source}-{rel_type}-{target}"
                    if rel_key not in seen_relations:
                        seen_relations.add(rel_key)
                        relations.append({
                            'source': source,
                            'target': target,
                            'type': rel_type,
                            'properties': {
                                'context': match.group()[:100]  # Store context
                            }
                        })
    
    logger.debug(f"Extracted {len(entities)} entities and {len(relations)} relations")
    return entities, relations


def _classify_entity_type(entity_name: str) -> str:
    """
    Simple heuristic-based entity type classification.
    In production, use proper NER models.
    
    Args:
        entity_name: Name of the entity
        
    Returns:
        Entity type label
    """
    # Very simple heuristics - replace with proper NER in production
    name_lower = entity_name.lower()
    
    # Common patterns
    if any(word in name_lower for word in ['inc', 'corp', 'company', 'ltd', 'llc', 'organization']):
        return 'Organization'
    elif any(word in name_lower for word in ['university', 'college', 'school', 'institute']):
        return 'Organization'
    elif any(word in name_lower for word in ['city', 'country', 'state', 'nation', 'republic']):
        return 'Location'
    elif len(entity_name.split()) == 2 and entity_name[0].isupper():
        # Potential person name (First Last)
        return 'Person'
    else:
        return 'Entity'  # Default type


def extract_entities_from_query(query: str) -> List[str]:
    """
    Extract potential entity names from a query.
    Used for KG traversal starting points.
    
    Args:
        query: User query text
        
    Returns:
        List of potential entity names
    """
    # Simple extraction - find capitalized phrases
    entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
    # Remove duplicates while preserving order
    seen = set()
    unique_entities = []
    for entity in entities:
        if entity not in seen and len(entity) > 2:
            seen.add(entity)
            unique_entities.append(entity)
    
    return unique_entities[:10]  # Limit to 10 entities

