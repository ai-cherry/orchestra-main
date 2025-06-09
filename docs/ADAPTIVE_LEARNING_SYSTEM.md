# Adaptive Learning System

## Overview

The Adaptive Learning System implements a framework that learns from user interactions to improve persona performance over time. It collects feedback, tracks performance metrics, and adjusts behavior based on learned patterns to create a continuously improving AI experience.

## Key Components

### 1. Feedback Collection

The system captures both explicit and implicit feedback from user interactions:

- **Explicit Feedback**: Direct ratings, likes/dislikes, or comments from users
- **Implicit Feedback**: Behavioral signals like continued engagement, follow-up questions, or abandonment
- **Contextual Metadata**: Information about the interaction context when feedback was given

### 2. Performance Metrics

The system tracks various performance dimensions for personas and features:

- **Relevance**: How well responses match user queries
- **Accuracy**: Factual correctness of information provided
- **Helpfulness**: Practical utility of responses
- **Clarity**: How understandable responses are
- **Efficiency**: Speed and directness of achieving user goals
- **Creativity**: Originality and innovation in responses
- **Safety**: Adherence to safety guidelines and user preferences

### 3. Adaptation Rules

Rules that modify persona behavior based on tracked metrics:

- **Threshold-Based**: Trigger adaptations when metrics cross defined thresholds
- **Comparison-Based**: Compare performance across different approaches
- **Persona-Specific**: Rules tailored to individual personas
- **Feature-Specific**: Rules focused on particular capabilities

### 4. Learning Models

Models that learn patterns from feedback and suggest adaptations:

- **Rule-Based Models**: Simple condition-action patterns
- **Statistical Models**: Track performance trends and correlations
- **Machine Learning Models**: Learn complex patterns from interaction data

## Implementation Details

The system is implemented in `src/learning/adaptive_learning_system.py` with the following key classes:

### UserFeedback

Represents feedback collected from user interactions:

```python
@dataclass
class UserFeedback:
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
```

### PerformanceMetric

Represents a tracked performance metric for a persona or feature:

```python
@dataclass
class PerformanceMetric:
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
```

### AdaptationRule

Represents a rule for adapting persona behavior based on metrics:

```python
@dataclass
class AdaptationRule:
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
```

### AdaptiveLearningSystem

Manages the collection of feedback, tracking of metrics, and adaptation of persona behavior:

```python
class AdaptiveLearningSystem:
    def __init__(self, storage_dir: str = "./adaptive_learning"):
        self.feedback_store: Dict[str, UserFeedback] = {}
        self.metrics_store: Dict[str, PerformanceMetric] = {}
        self.rules: Dict[str, AdaptationRule] = {}
        self.models: Dict[str, LearningModel] = {}
        self.storage_dir = storage_dir
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        os.makedirs(os.path.join(storage_dir, "models"), exist_ok=True)
```

## Key Functions

### Collecting Feedback

```python
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
```

### Managing Adaptation Rules

```python
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

def get_applicable_rules(
    self,
    persona_id: Optional[str] = None,
    feature_id: Optional[str] = None
) -> List[AdaptationRule]:
    """Get rules that should be applied based on current metrics."""
    applicable_rules = []
    
    # Filter rules by persona and feature
    candidate_rules = [
        rule for rule in self.rules.values()
        if (persona_id is None or rule.persona_id is None or rule.persona_id == persona_id) and
           (feature_id is None or rule.feature_id is None or rule.feature_id == feature_id)
    ]
    
    # Check each rule against current metrics
    for rule in candidate_rules:
        if not rule.enabled:
            continue
        
        # Find the relevant metric
        metric_id = None
        if rule.persona_id and rule.metric_category:
            metric_id = f"{rule.persona_id}_{rule.metric_category.value}"
        elif rule.feature_id and rule.metric_category:
            metric_id = f"{rule.feature_id}_{rule.metric_category.value}"
        
        if metric_id and metric_id in self.metrics_store:
            metric = self.metrics_store[metric_id]
            if rule.should_apply(metric.value):
                applicable_rules.append(rule)
    
    return applicable_rules
```

### Training and Using Learning Models

```python
def train_model(
    self,
    model_id: str,
    model_type: str = "rule_based",
    persona_id: Optional[str] = None,
    feature_id: Optional[str] = None
) -> bool:
    """Train a learning model on collected feedback."""
    # Get relevant feedback
    feedback_data = []
    for feedback in self.feedback_store.values():
        if ((persona_id is None or feedback.persona_id == persona_id) and
            (feature_id is None or 
             (feedback.metadata and feedback.metadata.get("feature_id") == feature_id))):
            feedback_data.append(feedback)
    
    # Create or get the model
    if model_id in self.models:
        model = self.models[model_id]
    else:
        if model_type == "rule_based":
            model = SimpleRuleBasedModel(model_id, persona_id)
        else:
            # Default to rule-based if type not recognized
            model = SimpleRuleBasedModel(model_id, persona_id)
        self.models[model_id] = model
    
    # Train the model
    model.train(feedback_data)
    
    # Save the model
    model_path = os.path.join(self.storage_dir, "models", f"{model_id}.pkl")
    model.save(os.path.join(self.storage_dir, "models"))
    
    return True

def get_adaptation_parameters(
    self,
    model_id: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Get adaptation parameters from a trained model."""
    if model_id not in self.models:
        return {}
    
    model = self.models[model_id]
    return model.predict(context)
```

## Usage Examples

### Collecting and Using Feedback

```python
from learning.adaptive_learning_system import (
    AdaptiveLearningSystem,
    FeedbackType,
    MetricCategory
)

# Initialize the learning system
learning_system = AdaptiveLearningSystem(storage_dir="./data/learning")

# Collect explicit feedback from a user
feedback_id = learning_system.collect_feedback(
    feedback_type=FeedbackType.EXPLICIT_POSITIVE,
    content="The response was very helpful and accurate",
    user_id="user123",
    session_id="session456",
    persona_id="cherry",
    metrics={
        MetricCategory.RELEVANCE: 0.9,
        MetricCategory.ACCURACY: 0.95,
        MetricCategory.HELPFULNESS: 0.85
    },
    metadata={
        "query_topic": "quantum_computing",
        "response_length": "medium"
    }
)

# Collect implicit feedback
learning_system.collect_feedback(
    feedback_type=FeedbackType.IMPLICIT_POSITIVE,
    user_id="user123",
    session_id="session456",
    persona_id="cherry",
    metrics={
        MetricCategory.ENGAGEMENT: 0.8
    },
    metadata={
        "time_spent": 120,  # seconds
        "follow_up_questions": 2
    }
)
```

### Creating and Applying Adaptation Rules

```python
# Add an adaptation rule
rule_id = learning_system.add_rule(
    name="Increase Detail Level",
    description="Provide more detailed responses when accuracy is rated low",
    metric_category=MetricCategory.ACCURACY,
    threshold=0.7,
    comparison="less_than",
    action="adjust_detail_level",
    parameters={"detail_level_adjustment": 0.3},
    persona_id="cherry"
)

# Get applicable rules for a persona
applicable_rules = learning_system.get_applicable_rules(persona_id="cherry")

# Apply rules to modify persona behavior
for rule in applicable_rules:
    if rule.action == "adjust_detail_level":
        detail_adjustment = rule.parameters.get("detail_level_adjustment", 0)
        # Apply this adjustment to the persona's behavior
        print(f"Adjusting detail level by {detail_adjustment}")
```

### Training and Using Learning Models

```python
# Train a model on collected feedback
learning_system.train_model(
    model_id="cherry_response_model",
    model_type="rule_based",
    persona_id="cherry"
)

# Use the model to get adaptation parameters
adaptation_params = learning_system.get_adaptation_parameters(
    model_id="cherry_response_model",
    context={
        "user_id": "user123",
        "topic": "quantum_computing",
        "recent_feedback": "positive"
    }
)

# Apply the adaptation parameters
print(f"Adaptation parameters: {adaptation_params}")
```

## Benefits

1. **Continuous Improvement**: Personas become more aligned with user preferences over time
2. **Data-Driven Adaptation**: Changes to behavior are based on actual user feedback
3. **Personalization**: Different adaptations can be applied for different users
4. **Measurable Performance**: Clear metrics track improvements over time
5. **Systematic Learning**: Structured approach to incorporating feedback

## Integration with Other Systems

The Adaptive Learning System integrates with:

1. **Persona Collaboration Framework**: Adapts persona behavior based on feedback
2. **Adaptive Context Management**: Learns which context elements are most relevant
3. **Unified Knowledge Graph**: Improves knowledge retrieval based on feedback

This system enables Orchestra AI to continuously improve its performance and better meet user needs over time.
