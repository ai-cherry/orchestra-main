#!/usr/bin/env python3
"""Auto-mode selection based on task analysis"""

import re

class AutoModeSelector:
    """Simple NLP-based mode selector"""
    
    MODE_PATTERNS = {
        "code": ["implement", "code", "function", "class", "method", "fix bug"],
        "architect": ["design", "architecture", "structure", "plan", "diagram"],
        "debug": ["error", "bug", "issue", "problem", "debug", "trace"],
        "review": ["review", "check", "analyze", "improve", "optimize"],
        "test": ["test", "verify", "validate", "assert", "coverage"]
    }
    
    @classmethod
    def suggest_mode(cls, task_description):
        """Suggest best mode based on task description"""
        task_lower = task_description.lower()
        scores = {}
        
        for mode, patterns in cls.MODE_PATTERNS.items():
            score = sum(1 for pattern in patterns if pattern in task_lower)
            if score > 0:
                scores[mode] = score
        
        if scores:
            best_mode = max(scores, key=scores.get)
            return best_mode, scores[best_mode]
        return "code", 0  # Default to code mode

if __name__ == "__main__":
    # Test the selector
    test_tasks = [
        "implement a new feature for user authentication",
        "debug the database connection error",
        "design the system architecture for microservices",
        "review and optimize the code performance"
    ]
    
    selector = AutoModeSelector()
    for task in test_tasks:
        mode, score = selector.suggest_mode(task)
        print(f"Task: {task[:50]}...")
        print(f"  Suggested mode: {mode} (score: {score})")
