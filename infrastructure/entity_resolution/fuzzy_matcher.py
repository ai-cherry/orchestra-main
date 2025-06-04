#!/usr/bin/env python3
"""
Enterprise Entity Resolution and Fuzzy Matching System
Advanced duplicate detection and data merging for Cherry AI Orchestrator

Features:
- Multi-algorithm fuzzy matching (Levenshtein, Jaro-Winkler, Soundex, etc.)
- Machine learning-based entity resolution
- Cross-system duplicate detection
- Intelligent data merging and conflict resolution
- Real-time matching API
- Batch processing for large datasets

Author: Cherry AI Team
Version: 1.0.0
"""

import os
import json
import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib

# Fuzzy matching libraries
try:
    from fuzzywuzzy import fuzz, process
    from fuzzywuzzy.utils import full_process
except ImportError:
    print("Warning: fuzzywuzzy not available. Install with: pip install fuzzywuzzy python-Levenshtein")

try:
    import jellyfish
except ImportError:
    print("Warning: jellyfish not available. Install with: pip install jellyfish")

try:
    import phonetics
except ImportError:
    print("Warning: phonetics not available. Install with: pip install phonetics")

# Machine learning libraries
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import DBSCAN
    import numpy as np
except ImportError:
    print("Warning: scikit-learn not available. Install with: pip install scikit-learn")

# Database integration
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database_layer'))
try:
    from enterprise_db_manager import EnterpriseDatabaseManager
except ImportError:
    print("Warning: Database manager not available")

logger = logging.getLogger(__name__)

@dataclass
class EntityRecord:
    """Represents a unified entity record across systems"""
    id: str
    source_system: str
    source_id: str
    entity_type: str  # person, company, opportunity, etc.
    
    # Core fields
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    
    # Address fields
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Additional data
    metadata: Optional[Dict[str, Any]] = None
    confidence_score: float = 1.0
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        if self.last_updated:
            data['last_updated'] = self.last_updated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntityRecord':
        """Create from dictionary"""
        if 'last_updated' in data and data['last_updated']:
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)

@dataclass
class MatchResult:
    """Represents a matching result between two entities"""
    entity1_id: str
    entity2_id: str
    similarity_score: float
    match_type: str  # exact, fuzzy, ml, composite
    matching_fields: List[str]
    confidence: float
    metadata: Optional[Dict[str, Any]] = None

class FuzzyMatcher:
    """Advanced fuzzy matching algorithms"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.vectorizer = None
        self._initialize_ml_components()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for fuzzy matching"""
        return {
            'similarity_thresholds': {
                'exact': 1.0,
                'high': 0.9,
                'medium': 0.7,
                'low': 0.5
            },
            'field_weights': {
                'email': 1.0,
                'phone': 0.9,
                'name': 0.8,
                'company': 0.7,
                'address': 0.6
            },
            'algorithms': {
                'levenshtein': True,
                'jaro_winkler': True,
                'soundex': True,
                'metaphone': True,
                'cosine': True
            },
            'preprocessing': {
                'normalize_case': True,
                'remove_punctuation': True,
                'remove_extra_spaces': True,
                'standardize_phone': True,
                'standardize_email': True
            }
        }
    
    def _initialize_ml_components(self):
        """Initialize machine learning components"""
        try:
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
        except:
            logger.warning("ML components not available")
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for matching"""
        if not text:
            return ""
        
        text = str(text)
        
        if self.config['preprocessing']['normalize_case']:
            text = text.lower()
        
        if self.config['preprocessing']['remove_punctuation']:
            text = re.sub(r'[^\w\s]', '', text)
        
        if self.config['preprocessing']['remove_extra_spaces']:
            text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def preprocess_email(self, email: str) -> str:
        """Preprocess email for matching"""
        if not email:
            return ""
        
        email = email.lower().strip()
        # Remove common email variations
        email = re.sub(r'\+.*@', '@', email)  # Remove + aliases
        return email
    
    def preprocess_phone(self, phone: str) -> str:
        """Preprocess phone number for matching"""
        if not phone:
            return ""
        
        # Remove all non-digits
        phone = re.sub(r'\D', '', phone)
        
        # Handle US phone numbers
        if len(phone) == 11 and phone.startswith('1'):
            phone = phone[1:]
        elif len(phone) == 10:
            pass  # Already in correct format
        
        return phone
    
    def exact_match(self, value1: str, value2: str) -> float:
        """Exact string matching"""
        if not value1 or not value2:
            return 0.0
        
        return 1.0 if value1 == value2 else 0.0
    
    def levenshtein_similarity(self, value1: str, value2: str) -> float:
        """Levenshtein distance similarity"""
        if not value1 or not value2:
            return 0.0
        
        try:
            return fuzz.ratio(value1, value2) / 100.0
        except:
            # Fallback implementation
            return self._simple_levenshtein(value1, value2)
    
    def jaro_winkler_similarity(self, value1: str, value2: str) -> float:
        """Jaro-Winkler similarity"""
        if not value1 or not value2:
            return 0.0
        
        try:
            return jellyfish.jaro_winkler_similarity(value1, value2)
        except:
            return 0.0
    
    def soundex_match(self, value1: str, value2: str) -> float:
        """Soundex phonetic matching"""
        if not value1 or not value2:
            return 0.0
        
        try:
            soundex1 = jellyfish.soundex(value1)
            soundex2 = jellyfish.soundex(value2)
            return 1.0 if soundex1 == soundex2 else 0.0
        except:
            return 0.0
    
    def metaphone_match(self, value1: str, value2: str) -> float:
        """Metaphone phonetic matching"""
        if not value1 or not value2:
            return 0.0
        
        try:
            meta1 = jellyfish.metaphone(value1)
            meta2 = jellyfish.metaphone(value2)
            return 1.0 if meta1 == meta2 else 0.0
        except:
            return 0.0
    
    def cosine_similarity_match(self, value1: str, value2: str) -> float:
        """Cosine similarity using TF-IDF vectors"""
        if not value1 or not value2 or not self.vectorizer:
            return 0.0
        
        try:
            # Fit and transform the texts
            tfidf_matrix = self.vectorizer.fit_transform([value1, value2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except:
            return 0.0
    
    def _simple_levenshtein(self, s1: str, s2: str) -> float:
        """Simple Levenshtein distance implementation"""
        if len(s1) < len(s2):
            return self._simple_levenshtein(s2, s1)
        
        if len(s2) == 0:
            return 0.0
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        max_len = max(len(s1), len(s2))
        return 1.0 - (previous_row[-1] / max_len)
    
    def composite_similarity(self, value1: str, value2: str, field_type: str = 'text') -> float:
        """Composite similarity using multiple algorithms"""
        if not value1 or not value2:
            return 0.0
        
        # Preprocess based on field type
        if field_type == 'email':
            value1 = self.preprocess_email(value1)
            value2 = self.preprocess_email(value2)
        elif field_type == 'phone':
            value1 = self.preprocess_phone(value1)
            value2 = self.preprocess_phone(value2)
        else:
            value1 = self.preprocess_text(value1)
            value2 = self.preprocess_text(value2)
        
        scores = []
        
        # Exact match (highest weight)
        exact_score = self.exact_match(value1, value2)
        if exact_score == 1.0:
            return 1.0
        
        # Fuzzy algorithms
        if self.config['algorithms']['levenshtein']:
            scores.append(self.levenshtein_similarity(value1, value2))
        
        if self.config['algorithms']['jaro_winkler']:
            scores.append(self.jaro_winkler_similarity(value1, value2))
        
        if self.config['algorithms']['soundex'] and field_type in ['name', 'company']:
            scores.append(self.soundex_match(value1, value2))
        
        if self.config['algorithms']['metaphone'] and field_type in ['name', 'company']:
            scores.append(self.metaphone_match(value1, value2))
        
        if self.config['algorithms']['cosine'] and len(value1) > 5 and len(value2) > 5:
            scores.append(self.cosine_similarity_match(value1, value2))
        
        # Return weighted average
        return sum(scores) / len(scores) if scores else 0.0

class EntityResolver:
    """Main entity resolution system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, 
                 db_manager: Optional[EnterpriseDatabaseManager] = None):
        self.config = config or self._default_config()
        self.db_manager = db_manager
        self.fuzzy_matcher = FuzzyMatcher(self.config.get('fuzzy_matching'))
        self.entity_cache = {}
        self.match_cache = {}
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for entity resolution"""
        return {
            'matching': {
                'similarity_threshold': 0.8,
                'confidence_threshold': 0.7,
                'max_candidates': 10,
                'enable_caching': True,
                'cache_ttl': 3600
            },
            'clustering': {
                'algorithm': 'dbscan',
                'eps': 0.3,
                'min_samples': 2,
                'enable_ml_clustering': True
            },
            'merging': {
                'conflict_resolution': 'most_recent',  # most_recent, highest_confidence, manual
                'preserve_source_data': True,
                'auto_merge_threshold': 0.95
            },
            'performance': {
                'batch_size': 1000,
                'parallel_processing': True,
                'max_workers': 4
            }
        }
    
    async def resolve_entity(self, entity: EntityRecord) -> List[MatchResult]:
        """Find potential matches for an entity"""
        # Check cache first
        cache_key = self._generate_cache_key(entity)
        if self.config['matching']['enable_caching'] and cache_key in self.match_cache:
            return self.match_cache[cache_key]
        
        # Get candidate entities
        candidates = await self._get_candidate_entities(entity)
        
        # Calculate similarities
        matches = []
        for candidate in candidates:
            match_result = await self._calculate_entity_similarity(entity, candidate)
            if match_result.similarity_score >= self.config['matching']['similarity_threshold']:
                matches.append(match_result)
        
        # Sort by similarity score
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Limit results
        max_candidates = self.config['matching']['max_candidates']
        matches = matches[:max_candidates]
        
        # Cache results
        if self.config['matching']['enable_caching']:
            self.match_cache[cache_key] = matches
        
        return matches
    
    async def _get_candidate_entities(self, entity: EntityRecord) -> List[EntityRecord]:
        """Get candidate entities for matching"""
        candidates = []
        
        # If we have a database manager, query for similar entities
        if self.db_manager and self.db_manager.postgresql_manager:
            # Query by email (exact match)
            if entity.email:
                email_candidates = await self._query_entities_by_field('email', entity.email)
                candidates.extend(email_candidates)
            
            # Query by phone (exact match)
            if entity.phone:
                phone = self.fuzzy_matcher.preprocess_phone(entity.phone)
                phone_candidates = await self._query_entities_by_field('phone', phone)
                candidates.extend(phone_candidates)
            
            # Query by name (fuzzy)
            if entity.name:
                name_candidates = await self._query_entities_by_name_fuzzy(entity.name)
                candidates.extend(name_candidates)
        
        # Remove duplicates and self-matches
        unique_candidates = {}
        for candidate in candidates:
            if candidate.id != entity.id:
                unique_candidates[candidate.id] = candidate
        
        return list(unique_candidates.values())
    
    async def _query_entities_by_field(self, field: str, value: str) -> List[EntityRecord]:
        """Query entities by specific field"""
        if not self.db_manager or not self.db_manager.postgresql_manager:
            return []
        
        query = f"""
        SELECT * FROM entities 
        WHERE {field} = %s 
        AND entity_type = %s
        LIMIT 50
        """
        
        try:
            results = await self.db_manager.postgresql_manager.execute_query(
                query, (value, 'person')  # Assuming person entity type
            )
            
            entities = []
            for row in results:
                entity = EntityRecord.from_dict(dict(row))
                entities.append(entity)
            
            return entities
        except Exception as e:
            logger.error(f"Error querying entities by {field}: {e}")
            return []
    
    async def _query_entities_by_name_fuzzy(self, name: str) -> List[EntityRecord]:
        """Query entities by name using fuzzy matching"""
        if not self.db_manager or not self.db_manager.postgresql_manager:
            return []
        
        # Use PostgreSQL's similarity function if available
        query = """
        SELECT * FROM entities 
        WHERE similarity(name, %s) > 0.3
        AND entity_type = %s
        ORDER BY similarity(name, %s) DESC
        LIMIT 20
        """
        
        try:
            results = await self.db_manager.postgresql_manager.execute_query(
                query, (name, 'person', name)
            )
            
            entities = []
            for row in results:
                entity = EntityRecord.from_dict(dict(row))
                entities.append(entity)
            
            return entities
        except Exception as e:
            # Fallback to LIKE query
            query = """
            SELECT * FROM entities 
            WHERE name ILIKE %s
            AND entity_type = %s
            LIMIT 20
            """
            
            try:
                results = await self.db_manager.postgresql_manager.execute_query(
                    query, (f'%{name}%', 'person')
                )
                
                entities = []
                for row in results:
                    entity = EntityRecord.from_dict(dict(row))
                    entities.append(entity)
                
                return entities
            except Exception as e2:
                logger.error(f"Error querying entities by name: {e2}")
                return []
    
    async def _calculate_entity_similarity(self, entity1: EntityRecord, 
                                         entity2: EntityRecord) -> MatchResult:
        """Calculate similarity between two entities"""
        field_scores = {}
        matching_fields = []
        
        # Email matching (highest priority)
        if entity1.email and entity2.email:
            email_score = self.fuzzy_matcher.composite_similarity(
                entity1.email, entity2.email, 'email'
            )
            field_scores['email'] = email_score
            if email_score > 0.9:
                matching_fields.append('email')
        
        # Phone matching
        if entity1.phone and entity2.phone:
            phone_score = self.fuzzy_matcher.composite_similarity(
                entity1.phone, entity2.phone, 'phone'
            )
            field_scores['phone'] = phone_score
            if phone_score > 0.9:
                matching_fields.append('phone')
        
        # Name matching
        if entity1.name and entity2.name:
            name_score = self.fuzzy_matcher.composite_similarity(
                entity1.name, entity2.name, 'name'
            )
            field_scores['name'] = name_score
            if name_score > 0.8:
                matching_fields.append('name')
        
        # Company matching
        if entity1.company and entity2.company:
            company_score = self.fuzzy_matcher.composite_similarity(
                entity1.company, entity2.company, 'company'
            )
            field_scores['company'] = company_score
            if company_score > 0.8:
                matching_fields.append('company')
        
        # Address matching
        if entity1.address and entity2.address:
            address_score = self.fuzzy_matcher.composite_similarity(
                entity1.address, entity2.address, 'address'
            )
            field_scores['address'] = address_score
            if address_score > 0.7:
                matching_fields.append('address')
        
        # Calculate weighted similarity
        total_score = 0.0
        total_weight = 0.0
        
        field_weights = self.fuzzy_matcher.config['field_weights']
        for field, score in field_scores.items():
            weight = field_weights.get(field, 0.5)
            total_score += score * weight
            total_weight += weight
        
        similarity_score = total_score / total_weight if total_weight > 0 else 0.0
        
        # Determine match type
        if similarity_score >= 0.95:
            match_type = 'exact'
        elif similarity_score >= 0.8:
            match_type = 'fuzzy'
        else:
            match_type = 'weak'
        
        # Calculate confidence
        confidence = self._calculate_confidence(field_scores, matching_fields)
        
        return MatchResult(
            entity1_id=entity1.id,
            entity2_id=entity2.id,
            similarity_score=similarity_score,
            match_type=match_type,
            matching_fields=matching_fields,
            confidence=confidence,
            metadata={
                'field_scores': field_scores,
                'algorithm': 'composite_fuzzy'
            }
        )
    
    def _calculate_confidence(self, field_scores: Dict[str, float], 
                            matching_fields: List[str]) -> float:
        """Calculate confidence score for a match"""
        # Base confidence on number of matching fields
        field_confidence = len(matching_fields) / 5.0  # Assuming 5 max fields
        
        # Boost confidence for high-value field matches
        high_value_fields = ['email', 'phone']
        high_value_matches = [f for f in matching_fields if f in high_value_fields]
        high_value_boost = len(high_value_matches) * 0.2
        
        # Average field scores
        avg_score = sum(field_scores.values()) / len(field_scores) if field_scores else 0.0
        
        # Combine factors
        confidence = min(1.0, (field_confidence + high_value_boost + avg_score) / 3.0)
        
        return confidence
    
    def _generate_cache_key(self, entity: EntityRecord) -> str:
        """Generate cache key for entity"""
        key_parts = [
            entity.entity_type,
            entity.email or '',
            entity.phone or '',
            entity.name or ''
        ]
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def merge_entities(self, entities: List[EntityRecord]) -> EntityRecord:
        """Merge multiple entity records into one"""
        if not entities:
            raise ValueError("No entities to merge")
        
        if len(entities) == 1:
            return entities[0]
        
        # Sort by confidence score (highest first)
        entities.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Start with the highest confidence entity
        merged = entities[0]
        
        # Merge fields from other entities
        for entity in entities[1:]:
            merged = self._merge_two_entities(merged, entity)
        
        # Update metadata
        merged.metadata = merged.metadata or {}
        merged.metadata['merged_from'] = [e.id for e in entities]
        merged.metadata['merge_timestamp'] = datetime.now().isoformat()
        merged.last_updated = datetime.now()
        
        return merged
    
    def _merge_two_entities(self, entity1: EntityRecord, entity2: EntityRecord) -> EntityRecord:
        """Merge two entity records"""
        # Use conflict resolution strategy
        strategy = self.config['merging']['conflict_resolution']
        
        merged = EntityRecord(
            id=entity1.id,  # Keep primary ID
            source_system='merged',
            source_id=f"{entity1.source_id}+{entity2.source_id}",
            entity_type=entity1.entity_type
        )
        
        # Merge each field
        fields = ['name', 'email', 'phone', 'company', 'title', 'address', 'city', 'state', 'country', 'postal_code']
        
        for field in fields:
            value1 = getattr(entity1, field)
            value2 = getattr(entity2, field)
            
            merged_value = self._resolve_field_conflict(value1, value2, strategy, entity1, entity2)
            setattr(merged, field, merged_value)
        
        # Merge metadata
        merged.metadata = {}
        if entity1.metadata:
            merged.metadata.update(entity1.metadata)
        if entity2.metadata:
            merged.metadata.update(entity2.metadata)
        
        # Use highest confidence score
        merged.confidence_score = max(entity1.confidence_score, entity2.confidence_score)
        
        # Use most recent update time
        if entity1.last_updated and entity2.last_updated:
            merged.last_updated = max(entity1.last_updated, entity2.last_updated)
        elif entity1.last_updated:
            merged.last_updated = entity1.last_updated
        elif entity2.last_updated:
            merged.last_updated = entity2.last_updated
        
        return merged
    
    def _resolve_field_conflict(self, value1: Any, value2: Any, strategy: str, 
                               entity1: EntityRecord, entity2: EntityRecord) -> Any:
        """Resolve conflict between two field values"""
        # If one is None, use the other
        if value1 is None:
            return value2
        if value2 is None:
            return value1
        
        # If they're the same, no conflict
        if value1 == value2:
            return value1
        
        # Apply resolution strategy
        if strategy == 'most_recent':
            if entity1.last_updated and entity2.last_updated:
                return value1 if entity1.last_updated >= entity2.last_updated else value2
            return value1  # Default to first entity
        
        elif strategy == 'highest_confidence':
            return value1 if entity1.confidence_score >= entity2.confidence_score else value2
        
        elif strategy == 'longest':
            if isinstance(value1, str) and isinstance(value2, str):
                return value1 if len(value1) >= len(value2) else value2
            return value1
        
        else:  # Default to first value
            return value1
    
    async def batch_resolve_entities(self, entities: List[EntityRecord]) -> Dict[str, List[MatchResult]]:
        """Resolve entities in batch for better performance"""
        results = {}
        
        batch_size = self.config['performance']['batch_size']
        
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            
            # Process batch
            batch_results = {}
            for entity in batch:
                matches = await self.resolve_entity(entity)
                batch_results[entity.id] = matches
            
            results.update(batch_results)
            
            # Log progress
            logger.info(f"Processed {min(i + batch_size, len(entities))}/{len(entities)} entities")
        
        return results
    
    async def cluster_entities(self, entities: List[EntityRecord]) -> List[List[EntityRecord]]:
        """Cluster entities using machine learning"""
        if not entities or len(entities) < 2:
            return [[entity] for entity in entities]
        
        try:
            # Create feature vectors
            features = []
            for entity in entities:
                feature_vector = self._create_feature_vector(entity)
                features.append(feature_vector)
            
            # Convert to numpy array
            X = np.array(features)
            
            # Apply DBSCAN clustering
            eps = self.config['clustering']['eps']
            min_samples = self.config['clustering']['min_samples']
            
            clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
            cluster_labels = clustering.fit_predict(X)
            
            # Group entities by cluster
            clusters = defaultdict(list)
            for i, label in enumerate(cluster_labels):
                clusters[label].append(entities[i])
            
            return list(clusters.values())
        
        except Exception as e:
            logger.error(f"Error in ML clustering: {e}")
            # Fallback to simple grouping
            return [[entity] for entity in entities]
    
    def _create_feature_vector(self, entity: EntityRecord) -> List[float]:
        """Create feature vector for ML clustering"""
        features = []
        
        # Text features (using simple hashing)
        text_fields = [entity.name, entity.email, entity.company, entity.title]
        for field in text_fields:
            if field:
                # Simple hash-based features
                hash_val = hash(field.lower()) % 1000
                features.append(hash_val / 1000.0)
            else:
                features.append(0.0)
        
        # Numeric features
        features.append(entity.confidence_score)
        
        # Categorical features (one-hot encoded)
        entity_types = ['person', 'company', 'opportunity', 'other']
        for et in entity_types:
            features.append(1.0 if entity.entity_type == et else 0.0)
        
        return features

# Example usage and testing
async def main():
    """Test the entity resolution system"""
    # Create test entities
    entity1 = EntityRecord(
        id="1",
        source_system="salesforce",
        source_id="sf_001",
        entity_type="person",
        name="John Smith",
        email="john.smith@example.com",
        phone="555-123-4567",
        company="Acme Corp"
    )
    
    entity2 = EntityRecord(
        id="2",
        source_system="hubspot",
        source_id="hs_001",
        entity_type="person",
        name="Jon Smith",
        email="j.smith@example.com",
        phone="5551234567",
        company="ACME Corporation"
    )
    
    # Initialize resolver
    resolver = EntityResolver()
    
    # Test similarity calculation
    match_result = await resolver._calculate_entity_similarity(entity1, entity2)
    print(f"Similarity: {match_result.similarity_score:.3f}")
    print(f"Matching fields: {match_result.matching_fields}")
    print(f"Confidence: {match_result.confidence:.3f}")
    
    # Test merging
    merged = await resolver.merge_entities([entity1, entity2])
    print(f"\nMerged entity:")
    print(f"Name: {merged.name}")
    print(f"Email: {merged.email}")
    print(f"Phone: {merged.phone}")
    print(f"Company: {merged.company}")

if __name__ == "__main__":
    asyncio.run(main())

