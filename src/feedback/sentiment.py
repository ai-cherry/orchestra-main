"""
Sentiment analysis for feedback text.

This module provides functionality for analyzing the sentiment of feedback text
using a combination of rule-based and ML-based approaches.
"""

import re
from typing import Dict, Tuple, Optional, List
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob

# Download NLTK resources if not already present
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')


class SentimentAnalyzer:
    """Sentiment analyzer for feedback text."""
    
    def __init__(self):
        """Initialize the sentiment analyzer."""
        self.vader = SentimentIntensityAnalyzer()
        
        # Common positive and negative phrases in feedback
        self.positive_phrases = [
            "great", "excellent", "good", "helpful", "useful", "amazing",
            "love", "perfect", "fantastic", "wonderful", "awesome",
            "thank you", "thanks", "appreciate", "well done", "impressive"
        ]
        
        self.negative_phrases = [
            "bad", "poor", "terrible", "useless", "unhelpful", "awful",
            "hate", "disappointing", "frustrating", "annoying", "broken",
            "not working", "doesn't work", "failed", "issue", "problem",
            "bug", "error", "crash", "slow", "confusing"
        ]
    
    def rule_based_sentiment(self, text: str) -> str:
        """
        Apply rule-based sentiment analysis.
        
        Args:
            text: The feedback text to analyze
            
        Returns:
            The sentiment classification ('positive', 'negative', 'neutral')
        """
        text_lower = text.lower()
        
        # Check for positive phrases
        positive_matches = sum(1 for phrase in self.positive_phrases if phrase in text_lower)
        
        # Check for negative phrases
        negative_matches = sum(1 for phrase in self.negative_phrases if phrase in text_lower)
        
        # Simple rule-based classification
        if positive_matches > negative_matches:
            return "positive"
        elif negative_matches > positive_matches:
            return "negative"
        else:
            return "neutral"
    
    def ml_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Apply ML-based sentiment analysis.
        
        Args:
            text: The feedback text to analyze
            
        Returns:
            A tuple of (sentiment, confidence_score)
        """
        # Use VADER for sentiment analysis
        vader_scores = self.vader.polarity_scores(text)
        compound_score = vader_scores['compound']
        
        # Use TextBlob as a secondary opinion
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity
        
        # Combine scores (weighted average)
        combined_score = (compound_score * 0.7) + (textblob_polarity * 0.3)
        
        # Determine sentiment and confidence
        if combined_score >= 0.2:
            sentiment = "positive"
            confidence = min(abs(combined_score) * 1.25, 1.0)
        elif combined_score <= -0.2:
            sentiment = "negative"
            confidence = min(abs(combined_score) * 1.25, 1.0)
        else:
            sentiment = "neutral"
            confidence = 1.0 - min(abs(combined_score) * 2.5, 0.8)
        
        return sentiment, confidence
    
    def adjust_with_context(
        self, 
        sentiment: str, 
        confidence: float, 
        context: Dict
    ) -> Tuple[str, float]:
        """
        Adjust sentiment based on context.
        
        Args:
            sentiment: The initial sentiment classification
            confidence: The initial confidence score
            context: Additional context for analysis
            
        Returns:
            A tuple of (adjusted_sentiment, adjusted_confidence)
        """
        # Adjust based on user history if available
        if 'user_history' in context:
            user_sentiment_bias = context.get('user_sentiment_bias', 0)
            
            # If user has a history of being overly negative or positive, adjust
            if user_sentiment_bias > 0.3 and sentiment == "negative":
                confidence *= 0.9  # Reduce confidence in negative sentiment
            elif user_sentiment_bias < -0.3 and sentiment == "positive":
                confidence *= 0.9  # Reduce confidence in positive sentiment
        
        # Adjust based on task type if available
        if 'task_type' in context:
            task_type = context['task_type']
            
            # Some tasks naturally get more negative feedback (e.g., technical support)
            if task_type == "technical_support" and sentiment == "negative":
                confidence *= 0.95
            
            # Some tasks naturally get more positive feedback (e.g., creative content)
            if task_type == "creative_content" and sentiment == "positive":
                confidence *= 0.95
        
        return sentiment, confidence
    
    def analyze(self, text: str, context: Optional[Dict] = None) -> Dict:
        """
        Analyze the sentiment of feedback text.
        
        Args:
            text: The feedback text to analyze
            context: Optional additional context for analysis
            
        Returns:
            A dictionary with sentiment analysis results
        """
        # Initial rule-based classification
        rule_sentiment = self.rule_based_sentiment(text)
        
        # ML-based sentiment analysis
        ml_sentiment, confidence = self.ml_sentiment(text)
        
        # Contextual adjustment if context provided
        if context:
            ml_sentiment, confidence = self.adjust_with_context(ml_sentiment, confidence, context)
        
        # Final decision (weighted combination)
        # If rule and ML agree, boost confidence
        if rule_sentiment == ml_sentiment:
            confidence = min(confidence * 1.2, 1.0)
            final_sentiment = ml_sentiment
        else:
            # If they disagree, trust ML more but reduce confidence
            confidence *= 0.8
            final_sentiment = ml_sentiment
        
        return {
            "sentiment": final_sentiment,
            "confidence": confidence,
            "rule_sentiment": rule_sentiment,
            "ml_sentiment": ml_sentiment
        }


def analyze_sentiment(text: str, context: Optional[Dict] = None) -> Dict:
    """
    Analyze the sentiment of feedback text.
    
    Args:
        text: The feedback text to analyze
        context: Optional additional context for analysis
        
    Returns:
        A dictionary with sentiment analysis results
    """
    analyzer = SentimentAnalyzer()
    return analyzer.analyze(text, context)
