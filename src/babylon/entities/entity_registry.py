from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
from .entity import Entity

class EntityRegistry:
    """Registry to maintain and track all game entities.
    
    Provides centralized management of entity lifecycle including:
    - Entity creation with unique ID generation
    - Entity updates with history tracking
    - Entity deletion with cleanup
    - Integration with ChromaDB operations
    """
    
    def __init__(self, chroma_collection: Any = None):
        self._entities: Dict[str, Entity] = {}
        self._deleted_entities: Dict[str, datetime] = {}
        self._chroma_collection = chroma_collection
        
    def create_entity(self, type: str, role: str) -> Entity:
        """Create a new entity with a unique ID.
        
        Args:
            type: Classification of the entity (e.g., 'Class', 'Organization')
            role: The entity's role in contradictions (e.g., 'Oppressor', 'Oppressed')
            
        Returns:
            Entity: The newly created entity
        """
        entity_id = str(uuid.uuid4())
        entity = Entity(id=entity_id, type=type, role=role)
        self._entities[entity_id] = entity
        
        # If ChromaDB collection exists, add entity to it
        if self._chroma_collection and entity.embedding is not None:
            entity.add_to_chromadb(self._chroma_collection)
            
        return entity
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Retrieve an entity by ID."""
        return self._entities.get(entity_id)
    
    def update_entity(self, entity_id: str, **kwargs) -> Optional[Entity]:
        """Update an entity's attributes.
        
        Args:
            entity_id: The ID of the entity to update
            **kwargs: Attribute names and values to update
            
        Returns:
            Optional[Entity]: The updated entity or None if not found
        """
        entity = self._entities.get(entity_id)
        if not entity:
            return None
            
        # Update attributes
        for attr, value in kwargs.items():
            if hasattr(entity, attr):
                setattr(entity, attr, value)
                
        # Update ChromaDB if collection exists
        if self._chroma_collection and entity.embedding is not None:
            entity.update_in_chromadb(self._chroma_collection)
            
        return entity
    
    def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity and record deletion time.
        
        Args:
            entity_id: The ID of the entity to delete
            
        Returns:
            bool: True if entity was deleted, False if not found
        """
        entity = self._entities.pop(entity_id, None)
        if not entity:
            return False
            
        # Record deletion time
        self._deleted_entities[entity_id] = datetime.now()
        
        # Remove from ChromaDB if collection exists
        if self._chroma_collection:
            entity.delete_from_chromadb(self._chroma_collection)
            
        return True
    
    def get_all_entities(self) -> List[Entity]:
        """Get all active entities."""
        return list(self._entities.values())
    
    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get all entities of a specific type."""
        return [e for e in self._entities.values() if e.type == entity_type]
    
    def get_entities_by_role(self, role: str) -> List[Entity]:
        """Get all entities with a specific role."""
        return [e for e in self._entities.values() if e.role == role]
    
    def get_deleted_entities(self) -> Dict[str, datetime]:
        """Get IDs and deletion times of deleted entities."""
        return self._deleted_entities.copy()
        
    def find_similar_entities(
        self,
        entity_id: str,
        n_results: int = 5,
        min_similarity: float = 0.7,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Entity]:
        """Find similar entities using kNN search with optional filtering.
        
        Args:
            entity_id: ID of the entity to find similarities for
            n_results: Maximum number of similar entities to return
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            filter_criteria: Optional dict of metadata filters (e.g., {"type": "Class"})
            
        Returns:
            List[Entity]: List of similar entities, sorted by similarity
            
        Raises:
            ValueError: If entity_id not found or ChromaDB not configured
        """
        if not self._chroma_collection:
            raise ValueError("ChromaDB collection not configured")
            
        entity = self.get_entity(entity_id)
        if not entity or entity.embedding is None:
            raise ValueError(f"Entity {entity_id} not found or has no embedding")
            
        # Construct query parameters
        query_params = {
            "query_embeddings": [entity.embedding],
            "n_results": n_results + 1,  # Add 1 to account for self-match
            "include": ["metadatas", "distances", "documents"]
        }
        
        # Add metadata filters if provided
        if filter_criteria:
            query_params["where"] = filter_criteria
            
        # Execute search
        results = self._chroma_collection.query(**query_params)
        
        # Process results
        similar_entities = []
        for i, (doc_id, distance) in enumerate(zip(results["ids"][0], results["distances"][0])):
            # Skip the query entity itself
            if doc_id == entity_id:
                continue
                
            # Convert distance to similarity score (1.0 - normalized_distance)
            similarity = 1.0 - (distance / 2.0)  # Assuming normalized distance
            
            # Apply similarity threshold
            if similarity >= min_similarity:
                found_entity = self.get_entity(doc_id)
                if found_entity:
                    similar_entities.append(found_entity)
                    
            if len(similar_entities) >= n_results:
                break
                
        return similar_entities
    
    def count_entities(self) -> int:
        """Get the total number of active entities."""
        return len(self._entities)