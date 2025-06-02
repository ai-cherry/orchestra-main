"""Smoke tests for orchestrator startup."""

from importlib import import_module

def test_main_import() -> None:
    """Ensure the main FastAPI app can be imported without side-effects."""
    module = import_module("core.orchestrator.src.main")  # type: ignore
    assert hasattr(module, "app"), "FastAPI app not found in main module"

def test_memory_factory_default() -> None:
    """Ensure the memory factory returns a default implementation."""
    factory = import_module("core.orchestrator.src.memory.factory")  # type: ignore
    default_mem = factory.get_default_memory()  # type: ignore[attr-defined]
    assert default_mem is not None, "Memory factory returned None"
