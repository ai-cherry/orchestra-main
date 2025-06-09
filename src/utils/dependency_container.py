from typing import Dict, Any, Type, Callable

class DependencyContainer:
    """Container for managing dependencies with proper injection."""
    _instance = None
    _dependencies: Dict[Any, Any] = {}

    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, interface, implementation):
        """Register an implementation for an interface."""
        self._dependencies[interface] = implementation

    def resolve(self, interface):
        """Resolve an implementation for an interface."""
        return self._dependencies.get(interface) 