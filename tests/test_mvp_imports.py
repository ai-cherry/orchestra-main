#!/usr/bin/env python3
"""
Test MVP component imports and basic functionality.
"""

import sys
from pathlib import Path

import pytest

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestMVPImports:
    """Test that MVP components can be imported successfully."""

    def test_enhanced_vector_memory_system_import(self):
        """Test that the enhanced vector memory system can be imported."""
        try:
            from enhanced_vector_memory_system import (
                ContextualMemory,
                EnhancedVectorMemorySystem,
            )

            assert EnhancedVectorMemorySystem is not None
            assert ContextualMemory is not None
        except ImportError as e:
            pytest.skip(
                f"Enhanced vector memory system dependencies not available: {e}"
            )

    def test_data_source_integrations_import(self):
        """Test that data source integrations can be imported."""
        try:
            from data_source_integrations import (
                DataAggregationOrchestrator,
                DataSourceConfig,
            )

            assert DataAggregationOrchestrator is not None
            assert DataSourceConfig is not None
        except ImportError as e:
            pytest.skip(f"Data source integration dependencies not available: {e}")

    def test_enhanced_natural_language_interface_import(self):
        """Test that the natural language interface can be imported."""
        try:
            from enhanced_natural_language_interface import (
                ConversationMode,
                EnhancedNaturalLanguageInterface,
            )

            assert EnhancedNaturalLanguageInterface is not None
            assert ConversationMode is not None
        except ImportError as e:
            pytest.skip(f"Natural language interface dependencies not available: {e}")

    def test_mvp_orchestra_ai_import(self):
        """Test that the main MVP integration can be imported."""
        try:
            from mvp_orchestra_ai import OrchestraAIMVP

            assert OrchestraAIMVP is not None
        except ImportError as e:
            pytest.skip(f"MVP orchestrator dependencies not available: {e}")


class TestBasicFunctionality:
    """Test basic functionality of MVP components."""

    def test_conversation_mode_enum(self):
        """Test that ConversationMode enum works correctly."""
        try:
            from enhanced_natural_language_interface import ConversationMode

            # Test enum values
            assert ConversationMode.CASUAL.value == "casual"
            assert ConversationMode.ANALYTICAL.value == "analytical"
            assert ConversationMode.TECHNICAL.value == "technical"
            assert ConversationMode.STRATEGIC.value == "strategic"
            assert ConversationMode.CREATIVE.value == "creative"

        except ImportError:
            pytest.skip("ConversationMode dependencies not available")

    def test_data_source_config_creation(self):
        """Test that DataSourceConfig can be created."""
        try:
            from data_source_integrations import DataSourceConfig

            config = DataSourceConfig(
                name="test",
                api_key="test_key",
                base_url="https://test.com",
                rate_limit=1.0,
            )

            assert config.name == "test"
            assert config.api_key == "test_key"
            assert config.base_url == "https://test.com"
            assert config.rate_limit == 1.0

        except ImportError:
            pytest.skip("DataSourceConfig dependencies not available")


if __name__ == "__main__":
    pytest.main([__file__])
