from enum import Enum
from typing import Dict, List, Optional
import inspect
import os

class ImplementationStatus(Enum):
    """Status of feature implementation."""
    COMPLETE = "complete"
    PARTIAL = "partial"
    PLANNED = "planned"
    NOT_IMPLEMENTED = "not_implemented"

class FeatureRegistry:
    """Registry of feature implementation status."""
    _registry: Dict[str, ImplementationStatus] = {}

    @staticmethod
    def scan_todos(root_dir: str = "../.."):
        """Scan codebase for TODOs and register them."""
        todos = []
        for dirpath, _, filenames in os.walk(root_dir):
            for fname in filenames:
                if fname.endswith('.py'):
                    fpath = os.path.join(dirpath, fname)
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            if 'TODO' in line:
                                todos.append((fpath, i, line.strip()))
        return todos

    @classmethod
    def mark_implemented(cls, feature_path: str):
        cls._registry[feature_path] = ImplementationStatus.COMPLETE

    @classmethod
    def set_status(cls, feature_path: str, status: ImplementationStatus):
        cls._registry[feature_path] = status

    @classmethod
    def get_status(cls, feature_path: str) -> Optional[ImplementationStatus]:
        return cls._registry.get(feature_path)

    @classmethod
    def summary(cls):
        return {k: v.value for k, v in cls._registry.items()} 