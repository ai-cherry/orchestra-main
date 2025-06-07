"""Smoke tests for conductor startup."""
    """Ensure the main FastAPI app can be imported without side-effects."""
    module = import_module("core.conductor.src.main")  # type: ignore
    assert hasattr(module, "app"), "FastAPI app not found in main module"

def test_memory_factory_default() -> None:
    """Ensure the memory factory returns a default implementation."""
    factory = import_module("core.conductor.src.memory.factory")  # type: ignore
    default_mem = factory.get_default_memory()  # type: ignore[attr-defined]
    assert default_mem is not None, "Memory factory returned None"
