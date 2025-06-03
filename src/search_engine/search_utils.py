#!/usr/bin/env python3
"""
Search Utilities
Common utilities shared across search strategies.
"""

import re
import hashlib
from typing import List, Dict, Any, Set
from datetime import datetime


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """Extract keywords from text."""
    # Simple keyword extraction
    words = re.findall(r'\b\w+\b', text.lower())
    return [word for word in words if len(word) >= min_length]


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate basic text similarity."""
    words1 = set(extract_keywords(text1))
    words2 = set(extract_keywords(text2))
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def deduplicate_results(results: List[Dict], similarity_threshold: float = 0.8) -> List[Dict]:
    """Remove duplicate results based on content similarity."""
    unique_results = []
    seen_hashes = set()
    
    for result in results:
        # Create content hash
        content = f"{result.get('title', '')} {result.get('content', '')}"
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        if content_hash not in seen_hashes:
            # Check similarity with existing results
            is_duplicate = False
            for existing in unique_results:
                existing_content = f"{existing.get('title', '')} {existing.get('content', '')}"
                similarity = calculate_text_similarity(content, existing_content)
                
                if similarity > similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_results.append(result)
                seen_hashes.add(content_hash)
    
    return unique_results


def rank_results_by_relevance(results: List[Dict], query: str) -> List[Dict]:
    """Rank results by relevance to query."""
    query_terms = set(extract_keywords(query))
    
    for result in results:
        # Calculate relevance score
        title_terms = set(extract_keywords(result.get("title", "")))
        content_terms = set(extract_keywords(result.get("content", "")))
        
        title_overlap = len(query_terms.intersection(title_terms))
        content_overlap = len(query_terms.intersection(content_terms))
        
        # Weight title matches higher
        relevance_score = (title_overlap * 2 + content_overlap) / max(len(query_terms), 1)
        
        result["relevance_score"] = relevance_score
        
        # Combine with existing score
        existing_score = result.get("score", 0.5)
        result["combined_score"] = (existing_score + relevance_score) / 2
    
    # Sort by combined score
    results.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
    
    return results


def format_search_snippet(content: str, query: str, max_length: int = 200) -> str:
    """Format search result snippet with query highlighting."""
    if not content:
        return ""
    
    # Find best snippet around query terms
    query_terms = extract_keywords(query)
    content_lower = content.lower()
    
    best_position = 0
    best_score = 0
    
    for term in query_terms:
        position = content_lower.find(term.lower())
        if position != -1:
            # Score based on how many query terms are nearby
            window_start = max(0, position - max_length // 2)
            window_end = min(len(content), position + max_length // 2)
            window_text = content_lower[window_start:window_end]
            
            score = sum(1 for term in query_terms if term.lower() in window_text)
            
            if score > best_score:
                best_score = score
                best_position = window_start
    
    # Extract snippet
    snippet_end = min(len(content), best_position + max_length)
    snippet = content[best_position:snippet_end]
    
    # Clean up
    if best_position > 0:
        snippet = "..." + snippet
    if snippet_end < len(content):
        snippet = snippet + "..."
    
    return snippet.strip()


def validate_search_query(query: str) -> Dict[str, Any]:
    """Validate and analyze search query."""
    validation = {
        "is_valid": True,
        "warnings": [],
        "suggestions": [],
        "query_type": "unknown",
        "estimated_complexity": "medium"
    }
    
    if not query or not query.strip():
        validation["is_valid"] = False
        validation["warnings"].append("Empty query")
        return validation
    
    # Analyze query characteristics
    query = query.strip()
    word_count = len(query.split())
    
    if word_count == 1:
        validation["query_type"] = "single_term"
        validation["estimated_complexity"] = "low"
    elif word_count <= 5:
        validation["query_type"] = "short_phrase"
        validation["estimated_complexity"] = "medium"
    else:
        validation["query_type"] = "long_phrase"
        validation["estimated_complexity"] = "high"
    
    # Check for special patterns
    if "?" in query:
        validation["query_type"] = "question"
        validation["suggestions"].append("Consider using deep search for questions")
    
    if any(word in query.lower() for word in ["how", "why", "what", "when", "where"]):
        validation["suggestions"].append("Question detected - deep search recommended")
    
    if any(word in query.lower() for word in ["creative", "brainstorm", "innovative"]):
        validation["suggestions"].append("Creative search mode recommended")
    
    return validation
