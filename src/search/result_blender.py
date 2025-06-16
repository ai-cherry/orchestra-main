"""
Orchestra AI - Search Result Blender
Intelligently blends and ranks search results from multiple sources
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import hashlib
import logging

logger = logging.getLogger(__name__)

class SearchResultBlender:
    """Blends search results from multiple sources with intelligent deduplication and ranking"""
    
    def __init__(self, redis_client, pinecone_index):
        self.redis = redis_client
        self.pinecone = pinecone_index
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
    async def blend_results(
        self,
        results_by_source: Dict[str, List[Dict]],
        query: str,
        persona: str,
        blend_ratio: Dict[str, float],
        persona_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Blend results from multiple sources with intelligent deduplication
        
        Args:
            results_by_source: Dictionary mapping source names to result lists
            query: Original search query
            persona: Active persona (cherry, sophia, karen)
            blend_ratio: Desired blend ratio between sources
            persona_weights: Optional persona-specific ranking weights
        
        Returns:
            Dictionary containing blended results and metadata
        """
        
        # 1. Flatten and tag all results
        all_results = []
        for source, results in results_by_source.items():
            for result in results:
                result['original_source'] = source
                result['result_id'] = self._generate_result_id(result)
                all_results.append(result)
        
        if not all_results:
            return {
                "results": [],
                "sources_used": list(results_by_source.keys()),
                "blend_ratio_applied": blend_ratio,
                "deduplication_count": 0
            }
        
        # 2. Deduplicate results
        unique_results, duplicate_count = await self._deduplicate_results(all_results)
        
        # 3. Calculate relevance scores
        scored_results = await self._calculate_relevance_scores(
            unique_results, 
            query, 
            persona, 
            persona_weights
        )
        
        # 4. Apply blend ratio
        blended_results = self._apply_blend_ratio(
            scored_results, 
            blend_ratio, 
            results_by_source.keys()
        )
        
        # 5. Final ranking and limiting
        final_results = sorted(
            blended_results, 
            key=lambda x: x['final_score'], 
            reverse=True
        )[:50]  # Limit to top 50
        
        # 6. Generate AI summary if needed
        summary = None
        if len(final_results) > 0:
            summary = await self._generate_result_summary(final_results[:10], query, persona)
        
        return {
            "results": final_results,
            "summary": summary,
            "sources_used": list(results_by_source.keys()),
            "blend_ratio_applied": blend_ratio,
            "deduplication_count": duplicate_count,
            "total_results_before_dedup": len(all_results),
            "total_results_after_dedup": len(unique_results)
        }
    
    def _generate_result_id(self, result: Dict) -> str:
        """Generate unique ID for a result based on URL and title"""
        content = f"{result.get('url', '')}{result.get('title', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _deduplicate_results(self, results: List[Dict]) -> Tuple[List[Dict], int]:
        """
        Deduplicate results using multiple strategies:
        1. Exact URL matching
        2. Title similarity
        3. Content similarity using TF-IDF
        """
        
        # Track seen URLs and similar content
        seen_urls = set()
        seen_titles = {}
        unique_results = []
        duplicate_count = 0
        
        # Extract text for similarity comparison
        texts = [f"{r.get('title', '')} {r.get('content', '')}" for r in results]
        
        # Compute TF-IDF vectors if we have enough results
        similarity_matrix = None
        if len(texts) > 5:
            try:
                tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
                similarity_matrix = cosine_similarity(tfidf_matrix)
            except Exception as e:
                logger.warning(f"TF-IDF calculation failed: {e}")
        
        for i, result in enumerate(results):
            url = result.get('url', '')
            title = result.get('title', '')
            
            # Check exact URL match
            if url and url in seen_urls:
                duplicate_count += 1
                continue
            
            # Check title similarity
            is_duplicate = False
            for seen_title, seen_idx in seen_titles.items():
                if self._calculate_string_similarity(title, seen_title) > 0.85:
                    # Merge metadata from duplicate
                    unique_results[seen_idx]['sources'] = unique_results[seen_idx].get('sources', [])
                    unique_results[seen_idx]['sources'].append(result['original_source'])
                    duplicate_count += 1
                    is_duplicate = True
                    break
            
            if is_duplicate:
                continue
            
            # Check content similarity using TF-IDF
            if similarity_matrix is not None:
                similarities = similarity_matrix[i]
                for j in range(i):
                    if similarities[j] > 0.8:  # High similarity threshold
                        duplicate_count += 1
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                result['sources'] = [result['original_source']]
                unique_results.append(result)
                if url:
                    seen_urls.add(url)
                if title:
                    seen_titles[title] = len(unique_results) - 1
        
        return unique_results, duplicate_count
    
    def _calculate_string_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings using Jaccard similarity"""
        if not s1 or not s2:
            return 0.0
        
        # Convert to lowercase and split into words
        words1 = set(s1.lower().split())
        words2 = set(s2.lower().split())
        
        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    async def _calculate_relevance_scores(
        self,
        results: List[Dict],
        query: str,
        persona: str,
        persona_weights: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """Calculate multi-factor relevance scores for each result"""
        
        for result in results:
            # Base relevance score (if provided by source)
            base_score = result.get('relevance_score', 0.5)
            
            # Query relevance using TF-IDF
            query_relevance = self._calculate_query_relevance(result, query)
            
            # Freshness score (newer content scores higher)
            freshness_score = self._calculate_freshness_score(result)
            
            # Source credibility score
            source_score = self._calculate_source_credibility(result['original_source'])
            
            # Persona-specific scoring
            persona_score = 1.0
            if persona_weights:
                if persona == 'sophia' and 'business_relevance' in persona_weights:
                    if any(term in str(result).lower() for term in 
                          ['business', 'rental', 'property', 'payment', 'financial']):
                        persona_score = persona_weights['business_relevance']
                
                elif persona == 'karen' and 'clinical_accuracy' in persona_weights:
                    if any(term in str(result).lower() for term in 
                          ['clinical', 'trial', 'medical', 'pharmaceutical', 'fda']):
                        persona_score = persona_weights['clinical_accuracy']
                
                elif persona == 'cherry' and 'creativity' in persona_weights:
                    # Cherry values diverse sources
                    persona_score = persona_weights.get('diversity', 0.8)
            
            # Combine scores with weights
            combined_score = (
                base_score * 0.3 +
                query_relevance * 0.3 +
                freshness_score * 0.1 +
                source_score * 0.2 +
                persona_score * 0.1
            )
            
            result['relevance_breakdown'] = {
                'base': base_score,
                'query_relevance': query_relevance,
                'freshness': freshness_score,
                'source_credibility': source_score,
                'persona_fit': persona_score
            }
            result['combined_score'] = combined_score
        
        return results
    
    def _calculate_query_relevance(self, result: Dict, query: str) -> float:
        """Calculate how relevant a result is to the query"""
        text = f"{result.get('title', '')} {result.get('content', '')}"
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        if not query_words:
            return 0.0
        
        # Count query word occurrences
        matches = sum(1 for word in query_words if word in text_words)
        relevance = matches / len(query_words)
        
        # Boost if query appears in title
        if all(word in result.get('title', '').lower() for word in query_words):
            relevance = min(1.0, relevance * 1.5)
        
        return relevance
    
    def _calculate_freshness_score(self, result: Dict) -> float:
        """Calculate freshness score based on publication date"""
        metadata = result.get('metadata', {})
        date_str = metadata.get('published_date') or metadata.get('date')
        
        if not date_str:
            return 0.5  # Default middle score if no date
        
        try:
            # Parse date and calculate age in days
            from dateutil import parser
            pub_date = parser.parse(date_str)
            age_days = (datetime.now() - pub_date).days
            
            # Exponential decay: newer content scores higher
            # Score = 1.0 for today, ~0.5 for 30 days old, ~0.1 for 365 days old
            score = np.exp(-age_days / 60)
            return max(0.1, min(1.0, score))
        except:
            return 0.5
    
    def _calculate_source_credibility(self, source: str) -> float:
        """Calculate credibility score based on source"""
        credibility_scores = {
            'Database': 0.9,  # Internal curated content
            'Google (SERP)': 0.8,
            'Exa AI': 0.85,  # Semantic search
            'DuckDuckGo': 0.7,
            'Venice AI (Uncensored)': 0.6,  # Lower due to unfiltered nature
            'Apify': 0.7,
            'ZenRows': 0.7
        }
        
        return credibility_scores.get(source, 0.5)
    
    def _apply_blend_ratio(
        self,
        results: List[Dict],
        blend_ratio: Dict[str, float],
        sources: List[str]
    ) -> List[Dict]:
        """Apply blend ratio to adjust final scores"""
        
        # Map sources to blend categories
        source_categories = {
            'Database': 'database',
            'DuckDuckGo': 'web',
            'Google (SERP)': 'web',
            'Exa AI': 'web',
            'Venice AI (Uncensored)': 'uncensored',
            'Apify': 'web',
            'ZenRows': 'web'
        }
        
        for result in results:
            source = result['original_source']
            category = source_categories.get(source, 'web')
            
            # Get blend weight for this category
            blend_weight = blend_ratio.get(category, 0.5)
            
            # Apply blend weight to combined score
            result['final_score'] = result['combined_score'] * blend_weight
            result['blend_category'] = category
            result['blend_weight'] = blend_weight
        
        return results
    
    async def _generate_result_summary(
        self,
        top_results: List[Dict],
        query: str,
        persona: str
    ) -> str:
        """Generate a brief AI summary of top results"""
        
        # For now, return a simple summary
        # In production, this would call an LLM
        summary_parts = []
        
        # Count sources
        sources = set(r['original_source'] for r in top_results)
        summary_parts.append(f"Found relevant results from {len(sources)} sources")
        
        # Top result info
        if top_results:
            top = top_results[0]
            summary_parts.append(f"Top result: '{top.get('title', 'Untitled')}' from {top['original_source']}")
        
        # Source distribution
        source_counts = {}
        for r in top_results:
            source = r['original_source']
            source_counts[source] = source_counts.get(source, 0) + 1
        
        summary_parts.append(f"Source distribution: {', '.join(f'{s} ({c})' for s, c in source_counts.items())}")
        
        return ". ".join(summary_parts)
