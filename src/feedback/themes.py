"""
Theme extraction for feedback analysis.

This module provides functionality for extracting common themes from feedback
using natural language processing techniques.
"""

from typing import Dict, List, Any, Optional
import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import numpy as np

# Download NLTK resources if not already present
try:
    nltk.data.find('punkt')
    nltk.data.find('stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')


class ThemeExtractor:
    """Theme extractor for feedback analysis."""
    
    def __init__(self):
        """Initialize the theme extractor."""
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer(
            max_df=0.85,
            min_df=2,
            max_features=5000,
            stop_words='english'
        )
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords from text.
        
        Args:
            text: The text to extract keywords from
            
        Returns:
            A list of keywords
        """
        # Tokenize and clean
        tokens = word_tokenize(text.lower())
        
        # Remove stopwords and non-alphabetic tokens
        keywords = [
            word for word in tokens 
            if word.isalpha() and word not in self.stop_words and len(word) > 2
        ]
        
        return keywords
    
    def cluster_by_similarity(
        self, 
        texts: List[str],
        eps: float = 0.5,
        min_samples: int = 2
    ) -> Dict[int, List[int]]:
        """
        Cluster feedback texts by similarity.
        
        Args:
            texts: List of feedback texts
            eps: DBSCAN epsilon parameter
            min_samples: DBSCAN min_samples parameter
            
        Returns:
            Dictionary mapping cluster IDs to lists of text indices
        """
        # Create TF-IDF matrix
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        # Perform clustering
        dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
        clusters = dbscan.fit_predict(tfidf_matrix)
        
        # Group by cluster
        cluster_map = {}
        for i, cluster_id in enumerate(clusters):
            if cluster_id == -1:  # Noise points
                continue
                
            if cluster_id not in cluster_map:
                cluster_map[cluster_id] = []
            
            cluster_map[cluster_id].append(i)
        
        return cluster_map
    
    def get_common_keywords(
        self, 
        indices: List[int], 
        all_keywords: List[List[str]]
    ) -> List[str]:
        """
        Get common keywords across multiple texts.
        
        Args:
            indices: Indices of texts to analyze
            all_keywords: List of keyword lists for all texts
            
        Returns:
            List of common keywords
        """
        # Flatten keywords from selected texts
        cluster_keywords = [word for i in indices for word in all_keywords[i]]
        
        # Count occurrences
        keyword_counts = Counter(cluster_keywords)
        
        # Return top keywords
        return [word for word, count in keyword_counts.most_common(10)]
    
    def generate_theme_label(
        self, 
        cluster_id: int, 
        indices: List[int], 
        all_keywords: List[List[str]]
    ) -> str:
        """
        Generate a label for a theme.
        
        Args:
            cluster_id: ID of the cluster
            indices: Indices of texts in the cluster
            all_keywords: List of keyword lists for all texts
            
        Returns:
            A theme label
        """
        common_keywords = self.get_common_keywords(indices, all_keywords)
        
        if not common_keywords:
            return f"Theme {cluster_id}"
        
        # Use the most common 1-3 keywords as the theme name
        theme_words = common_keywords[:min(3, len(common_keywords))]
        return " ".join(word.capitalize() for word in theme_words)
    
    def extract_themes(self, feedback_batch: List[Dict[str, Any]]) -> Dict[str, Dict]:
        """
        Extract common themes from a batch of feedback.
        
        Args:
            feedback_batch: List of feedback dictionaries with 'id' and 'text' keys
            
        Returns:
            Dictionary mapping theme names to theme information
        """
        if not feedback_batch:
            return {}
        
        # Extract texts and keywords
        texts = [item['text'] for item in feedback_batch]
        keywords = [self.extract_keywords(text) for text in texts]
        
        # Cluster feedback
        clusters = self.cluster_by_similarity(texts)
        
        # Generate themes
        themes = {}
        for cluster_id, feedback_indices in clusters.items():
            theme_name = self.generate_theme_label(cluster_id, feedback_indices, keywords)
            
            themes[theme_name] = {
                'feedback_ids': [feedback_batch[i]['id'] for i in feedback_indices],
                'keywords': self.get_common_keywords(feedback_indices, keywords),
                'count': len(feedback_indices)
            }
        
        return themes


def extract_themes(feedback_batch: List[Dict[str, Any]]) -> Dict[str, Dict]:
    """
    Extract common themes from a batch of feedback.
    
    Args:
        feedback_batch: List of feedback dictionaries with 'id' and 'text' keys
        
    Returns:
        Dictionary mapping theme names to theme information
    """
    extractor = ThemeExtractor()
    return extractor.extract_themes(feedback_batch)
