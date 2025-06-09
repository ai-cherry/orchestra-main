"""
Adaptive Learning System for Orchestra AI

This module implements a system that learns from user interactions to improve persona performance over time,
collecting feedback, tracking metrics, and adjusting behavior based on learned patterns.
"""

from typing import Dict, List, Optional, Any, Tuple, Set, Union
import uuid
from datetime import datetime
import json
import numpy as np
from enum import Enum
from dataclasses import dataclass, field
import os
import pickle

class FeedbackType(str, Enum):
    EXPLICIT_POSITIVE = "explicit_positive"
    EXPLICIT_NEGATIVE = "explicit_negative"
    IMPLICIT_POSITIVE = "implicit_positive"
    IMPLICIT_NEGATIVE = "implicit_negative"
    NEUTRAL = "neutral"

class MetricCategory(str, Enum):
    RELEVANCE = "relevance"
    ACCURACY = "accuracy"
    HELPFULNESS = "helpfulness"
    CLARITY = "clarity"
    EFFICIENCY = "efficiency"
    CREATIVITY = "creativity"
    SAFETY = "safety"

@dataclass
class UserFeedback:
    """Represents feedback collected from user interactions."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "anonymous"
    session_id: str = ""
    feedback_type: FeedbackType = FeedbackType.NEUTRAL
    content: str = ""
    context_id: Optional[str] = None
    persona_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metrics: Dict[MetricCategory, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert feedback to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "feedback_type": self.feedback_type,
            "content": self.content,
            "context_id": self.context_id,
            "persona_id": self.persona_id,
            "timestamp": self.timestamp,
            "metrics": {k.value: v for k, v in self.metrics.items()},
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserFeedback':
        """Create feedback from dictionary representation."""
        metrics = {MetricCategory(k): v for k, v in data.get("metrics", {}).items()}
        feedback = cls(
            id=data["id"],
            user_id=data["user_id"],
            session_id=data["session_id"],
            feedback_type=data["feedback_type"],
            content=data["content"],
            context_id=data.get("context_id"),
            persona_id=data.get("persona_id"),
            timestamp=data["timestamp"],
            metrics=metrics,
            metadata=data.get("metadata", {})
        )
        return feedback

@dataclass
class PerformanceMetric:
    """Represents a tracked performance metric for a persona or feature."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    category: MetricCategory = MetricCategory.RELEVANCE
    value: float = 0.0
    count: int = 0
    persona_id: Optional[str] = None
    feature_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update(self, new_value: float) -> None:
        """Update the metric with a new value."""
        # Calculate running average
        self.value = ((self.value * self.count) + new_value) / (self.count + 1)
        self.count += 1
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "value": self.value,
            "count": self.count,
            "persona_id": self.persona_id,
            "feature_id": self.feature_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetric':
        """Create metric from dictionary representation."""
        metric = cls(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            value=data["value"],
            count=data["count"],
            persona_id=data.get("persona_id"),
            feature_id=data.get("feature_id"),
            timestamp=data["timestamp"],
            metadata=data.get("metadata", {})
        )
        return metric

@dataclass
class AdaptationRule:
    """Represents a rule for adapting persona behavior based on metrics."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    metric_category: MetricCategory = MetricCategory.RELEVANCE
    threshold: float = 0.5
    comparison: str = "less_than"  # "less_than", "greater_than", "equal_to"
    action: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    persona_id: Optional[str] = None
    feature_id: Optional[str] = None
    
    def should_apply(self, metric_value: float) -> bool:
        """Check if this rule should be applied based on the metric value."""
        if not self.enabled:
            return False
        
        if self.comparison == "less_than":
            return metric_value < self.threshold
        elif self.comparison == "greater_than":
            return metric_value > self.threshold
        elif self.comparison == "equal_to":
            return abs(metric_value - self.threshold) < 0.001
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "metric_category": self.metric_category,
            "threshold": self.threshold,
            "comparison": self.comparison,
            "action": self.action,
            "parameters": self.parameters,
            "enabled": self.enabled,
            "persona_id": self.persona_id,
            "feature_id": self.feature_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdaptationRule':
        """Create rule from dictionary representation."""
        rule = cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            metric_category=data["metric_category"],
            threshold=data["threshold"],
            comparison=data["comparison"],
            action=data["action"],
            parameters=data.get("parameters", {}),
            enabled=data["enabled"],
            persona_id=data.get("persona_id"),
            feature_id=data.get("feature_id")
        )
        return rule

class LearningModel:
    """Base class for learning models that adapt persona behavior."""
    
    def __init__(self, model_id: str, persona_id: Optional[str] = None):
        self.model_id = model_id
        self.persona_id = persona_id
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.version = "1.0.0"
        self.metadata: Dict[str, Any] = {}
    
    def train(self, feedback_data: List[UserFeedback]) -> None:
        """Train the model on feedback data."""
        raise NotImplementedError("Subclasses must implement train method")
    
    def predict(self, context: Dict[str, Any]) -> Any:
        """Make a prediction based on context."""
        raise NotImplementedError("Subclasses must implement predict method")
    
    def save(self, directory: str) -> str:
        """Save the model to disk."""
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, f"{self.model_id}.pkl")
        
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        
        return filepath
    
    @classmethod
    def load(cls, filepath: str) -> 'LearningModel':
        """Load a model from disk."""
        with open(filepath, 'rb') as f:
            model = pickle.load(f)
        
        return model

class SimpleRuleBasedModel(LearningModel):
    """A simple rule-based learning model."""
    
    def __init__(self, model_id: str, persona_id: Optional[str] = None):
        super().__init__(model_id, persona_id)
        self.rules: Dict[str, Dict[str, float]] = {}
        self.default_values: Dict[str, float] = {}
    
    def train(self, feedback_data: List[UserFeedback]) -> None:
        """Train the model on feedback data."""
        # Group feedback by feature/action
        feature_feedback: Dict[str, List[Tuple[FeedbackType, Dict[MetricCategory, float]]]] = {}
        
        for feedback in feedback_data:
            feature = feedback.metadata.get("feature", "default")
            if feature not in feature_feedback:
                feature_feedback[feature] = []
            
            feature_feedback[feature].append((feedback.feedback_type, feedback.metrics))
        
        # Update rules based on feedback
        for feature, feedbacks in feature_feedback.items():
            if feature not in self.rules:
                self.rules[feature] = {}
            
            # Calculate average metrics for each feedback type
            for feedback_type, metrics in feedbacks:
                for category, value in metrics.items():
                    key = f"{feedback_type}_{category}"
                    if key not in self.rules[feature]:
                        self.rules[feature][key] = value
                    else:
                        # Simple running average
                        self.rules[feature][key] = (self.rules[feature][key] + value) / 2
        
        self.updated_at = datetime.now().isoformat()
    
    def predict(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Predict adaptation parameters based on context."""
        feature = context.get("feature", "default")
        
        if feature in self.rules:
            return self.rules[feature]
        
        return self.default_values

class AdaptiveLearningSystem:
    """Manages the collection of feedback, tracking of metrics, and adaptation of persona behavior."""
    
    def __init__(self, storage_dir: str = "./adaptive_learning"):
        self.feedback_store: Dict[str, UserFeedback] = {}
        self.metrics_store: Dict[str, PerformanceMetric] = {}
        self.rules: Dict[str, AdaptationRule] = {}
        self.models: Dict[str, LearningModel] = {}
        self.storage_dir = storage_dir
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        os.makedirs(os.path.join(storage_dir, "models"), exist_ok=True)
    
    def collect_feedback(
        self,
        feedback_type: FeedbackType,
        content: str = "",
        user_id: str = "anonymous",
        session_id: str = "",
        context_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        metrics: Dict[MetricCategory, float] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Collect and store user feedback."""
        feedback = UserFeedback(
            user_id=user_id,
            session_id=session_id,
            feedback_type=feedback_type,
            content=content,
            context_id=context_id,
            persona_id=persona_id,
            metrics=metrics or {},
            metadata=metadata or {}
        )
        
        self.feedback_store[feedback.id] = feedback
        
        # Update metrics based on feedback
        self._update_metrics_from_feedback(feedback)
        
        return feedback.id
    
    def _update_metrics_from_feedback(self, feedback: UserFeedback) -> None:
        """Update performance metrics based on feedback."""
        # Update persona-specific metrics
        if feedback.persona_id:
            for category, value in feedback.metrics.items():
                metric_id = f"{feedback.persona_id}_{category.value}"
                
                if metric_id not in self.metrics_store:
                    # Create new metric
                    self.metrics_store[metric_id] = PerformanceMetric(
                        name=f"{category.value.capitalize()} for {feedback.persona_id}",
                        category=category,
                        persona_id=feedback.persona_id
                    )
                
                # Update existing metric
                self.metrics_store[metric_id].update(value)
        
        # Update feature-specific metrics if applicable
        feature_id = feedback.metadata.get("feature_id")
        if feature_id:
            for category, value in feedback.metrics.items():
                metric_id = f"{feature_id}_{category.value}"
                
                if metric_id not in self.metrics_store:
                    # Create new metric
                    self.metrics_store[metric_id] = PerformanceMetric(
                        name=f"{category.value.capitalize()} for {feature_id}",
                        category=category,
                        feature_id=feature_id
                    )
                
                # Update existing metric
                self.metrics_store[metric_id].update(value)
    
    def get_feedback(self, feedback_id: str) -> Optional[UserFeedback]:
        """Get feedback by ID."""
        return self.feedback_store.get(feedback_id)
    
    def get_feedback_by_user(self, user_id: str) -> List[UserFeedback]:
        """Get all feedback from a specific user."""
        return [f for f in self.feedback_store.values() if f.user_id == user_id]
    
    def get_feedback_by_persona(self, persona_id: str) -> List[UserFeedback]:
        """Get all feedback for a specific persona."""
        return [f for f in self.feedback_store.values() if f.persona_id == persona_id]
    
    def add_metric(
        self,
        name: str,
        category: MetricCategory,
        initial_value: float = 0.0,
        persona_id: Optional[str] = None,
        feature_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add a new performance metric."""
        metric = PerformanceMetric(
            name=name,
            category=category,
            value=initial_value,
            persona_id=persona_id,
            feature_id=feature_id,
            metadata=metadata or {}
        )
        
        self.metrics_store[metric.id] = metric
        return metric.id
    
    def update_metric(self, metric_id: str, value: float) -> bool:
        """Update a metric with a new value."""
        if metric_id in self.metrics_store:
            self.metrics_store[metric_id].update(value)
            return True
        return False
    
    def get_metric(self, metric_id: str) -> Optional[PerformanceMetric]:
        """Get a metric by ID."""
        return self.metrics_store.get(metric_id)
    
    def get_metrics_by_persona(self, persona_id: str) -> Dict[str, PerformanceMetric]:
        """Get all metrics for a specific persona."""
        return {
            k: v for k, v in self.metrics_store.items()
            if v.persona_id == persona_id
        }
    
    def get_metrics_by_category(self, category: MetricCategory) -> Dict[str, PerformanceMetric]:
        """Get all metrics of a specific category."""
        return {
            k: v for k, v in self.metrics_store.items()
            if v.category == category
        }
    
    def add_rule(
        self,
        name: str,
        description: str,
        metric_category: MetricCategory,
        threshold: float,
        comparison: str,
        action: str,
        parameters: Dict[str, Any] = None,
        persona_id: Optional[str] = None,
        feature_id: Optional[str] = None
    ) -> str:
        """Add a new adaptation rule."""
        rule = AdaptationRule(
            name=name,
            description=description,
            metric_category=metric_category,
            threshold=threshold,
            comparison=comparison,
            action=action,
            parameters=parameters or {},
            persona_id=persona_id,
            feature_id=feature_id
        )
        
        self.rules[rule.id] = rule
        return rule.id
    
    def get_rule(self, rule_id: str) -> Optional[AdaptationRule]:
        """Get a rule by ID."""
        return self.rules.get(rule_id)
    
    def get_rules_by_persona(self, persona_id: str) -> Dict[str, AdaptationRule]:
        """Get all rules for a specific persona."""
        return {
            k: v for k, v in self.rules.items()
            if v.persona_id == persona_id
        }
    
    def get_applicable_rules(
        self,
        persona_id: Optional[str] = None,
        feature_id: Optional[str] = None
    ) -> List[AdaptationRule]:
        """Get rules that apply to the given persona or feature."""
        applicable_rules = []
        
        for rule in self.rules.values():
            # Skip disabled rules
            if not rule.enabled:
                continue
            
            # Check if rule applies to this persona or feature
            persona_match = rule.persona_id is None or rule.persona_id == persona_id
            feature_match = rule.feature_id is None or rule.feature_id == feature_id
            
            if persona_match and feature_match:
                applicable_rules.append(rule)
        
        return applicable_rules
    
    def evaluate_rules(
        self,
        persona_id: Optional[str] = None,
        feature_id: Optional[str] = None
    ) -> List[Tuple[AdaptationRule, bool]]:
        """Evaluate rules against current metrics."""
        results = []
        
        # Get applicable rules
        rules = self.get_applicable_rules(persona_id, feature_id)
        
        for rule in rules:
            # Find relevant metrics
            metric_id = None
            if rule.persona_id and rule.metric_category:
                metric_id = f"{rule.persona_id}_{rule.metric_category.value}"
            elif rule.feature_id and rule.metric_category:
                metric_id = f"{rule.feature_id}_{rule.metric_category.value}"
            
            # Skip if no relevant metric found
            if not metric_id or metric_id not in self.metrics_store:
                results.append((rule, False))
                continue
            
            # Evaluate rule against metric
            metric = self.metrics_store[metric_id]
            should_apply = rule.should_apply(metric.value)
            results.append((rule, should_apply))
        
        return results
    
    def get_adaptations(
        self,
        persona_id: Optional[str] = None,
        feature_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get adaptation parameters based on rules and metrics."""
        adaptations = {}
        
        # Evaluate rules
        rule_results = self.evaluate_rules(persona_id, feature_id)
        
        # Apply rules that should be applied
        for rule, should_apply in rule_results:
            if should_apply:
                # Extract action and parameters
                action = rule.action
                parameters = rule.parameters
                
                # Add to adaptations
                if action not in adaptations:
                    adaptations[action] = parameters
                else:
                    # Merge parameters if action already exists
                    adaptations[action].update(parameters)
        
        return adaptations
    
    def create_model(
        self,
        model_type: str,
        model_id: str,
        persona_id: Optional[str] = None
    ) -> LearningModel:
        """Create a new learning model."""
        if model_type == "rule_based":
            model = SimpleRuleBasedModel(model_id, persona_id)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        self.models[model_id] = model
        return model
    
    def get_model(self, model_id: str) -> Optional[LearningModel]:
        """Get a model by ID."""
        return self.models.get(model_id)
    
    def train_model(self, model_id: str, feedback_ids: List[str] = None) -> bool:
        """Train a model on feedback data."""
        if model_id not in self.models:
            return False
        
        model = self.models[model_id]
        
        # Collect feedback data
        if feedback_ids:
            feedback_data = [
                self.feedback_store[fid] for fid in feedback_ids
                if fid in self.feedback_store
            ]
        else:
            # Use all feedback for this persona
            persona_id = model.persona_id
            if persona_id:
                feedback_data = self.get_feedback_by_persona(persona_id)
            else:
                feedback_data = list(self.feedback_store.values())
        
        # Train the model
        model.train(feedback_data)
        
        # Save the model
        model.save(os.path.join(self.storage_dir, "models"))
        
        return True
    
    def get_model_prediction(self, model_id: str, context: Dict[str, Any]) -> Any:
        """Get a prediction from a model."""
        if model_id not in self.models:
            return None
        
        model = self.models[model_id]
        return model.predict(context)
    
    def save_state(self) -> str:
        """Save the current state to disk."""
        state = {
            "feedback": {k: v.to_dict() for k, v in self.feedback_store.items()},
            "metrics": {k: v.to_dict() for k, v in self.metrics_store.items()},
            "rules": {k: v.to_dict() for k, v in self.rules.items()},
            "model_ids": list(self.models.keys())
        }
        
        filepath = os.path.join(self.storage_dir, "state.json")
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        # Save models separately
        for model_id, model in self.models.items():
            model.save(os.path.join(self.storage_dir, "models"))
        
        return filepath
    
    def load_state(self, filepath: str) -> bool:
        """Load state from disk."""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            # Load feedback
            self.feedback_store = {
                k: UserFeedback.from_dict(v) for k, v in state["feedback"].items()
            }
            
            # Load metrics
            self.metrics_store = {
                k: PerformanceMetric.from_dict(v) for k, v in state["metrics"].items()
            }
            
            # Load rules
            self.rules = {
                k: AdaptationRule.from_dict(v) for k, v in state["rules"].items()
            }
            
            # Load models
            models_dir = os.path.join(self.storage_dir, "models")
            for model_id in state["model_ids"]:
                model_path = os.path.join(models_dir, f"{model_id}.pkl")
                if os.path.exists(model_path):
                    self.models[model_id] = LearningModel.load(model_path)
            
            return True
        except Exception as e:
            print(f"Error loading state: {e}")
            return False
    
    def get_learning_registry(self) -> Dict[str, Any]:
        """Get a summary of the learning system state."""
        return {
            "feedback_count": len(self.feedback_store),
            "metrics_count": len(self.metrics_store),
            "rules_count": len(self.rules),
            "models_count": len(self.models),
            "personas": list(set(f.persona_id for f in self.feedback_store.values() if f.persona_id)),
            "features": list(set(f.metadata.get("feature_id") for f in self.feedback_store.values() if "feature_id" in f.metadata)),
            "metric_categories": list(set(m.category for m in self.metrics_store.values())),
            "model_ids": list(self.models.keys())
        }
