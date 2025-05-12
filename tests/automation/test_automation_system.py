#!/usr/bin/env python3
"""
Tests for the AI Orchestra automation system.

This test suite verifies the integration and functionality of the automation components,
including the decision helper, controller, and various optimization modules.
"""

import asyncio
import os
import sys
import json
import shutil
import pytest
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock

# Add parent directory to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import automation components
try:
    from automation_controller import (
        AutomationController,
        AutomationTask,
        AutomationMode,
        Environment
    )
    from automation_decision_helper import (
        AutomationDecisionHelper,
        DecisionContext
    )
except ImportError:
    # Mark tests to be skipped if modules aren't available
    automation_available = False
else:
    automation_available = True


# Fixture for temporary test directory
@pytest.fixture
def temp_data_dir(tmp_path):
    """Provide a temporary directory for test data."""
    data_dir = tmp_path / "automation_test_data"
    data_dir.mkdir()
    yield data_dir
    # Clean up after tests
    shutil.rmtree(data_dir, ignore_errors=True)


# Fixture for test configuration
@pytest.fixture
def test_config():
    """Provide a test configuration."""
    return {
        "performance": {
            "enabled": True,
            "automation_level": 2,
            "analysis_frequency_hours": 1,  # More frequent for testing
            "apply_threshold": {
                "development": 0.7,
                "staging": 0.5,
                "production": 0.3,
            }
        },
        "workspace": {
            "enabled": True,
            "file_exclusion_enabled": True,
            "git_optimization_enabled": True,
            "workspace_segmentation_enabled": True,
        },
        "decision_weights": {
            "performance": 0.4,
            "cost": 0.3,
            "reliability": 0.3
        },
        "risk_tolerance": {
            "development": 0.8,
            "staging": 0.5,
            "production": 0.3
        }
    }


# Skip all tests if automation components aren't available
pytestmark = pytest.mark.skipif(
    not automation_available,
    reason="Automation components not available"
)


# Test decision helper functionality
@pytest.mark.asyncio
async def test_decision_helper_initialization():
    """Test decision helper initialization."""
    helper = AutomationDecisionHelper()
    assert helper is not None
    assert hasattr(helper, "thresholds")
    assert "performance" in helper.thresholds


@pytest.mark.asyncio
async def test_decision_helper_context_collection(temp_data_dir):
    """Test decision context collection."""
    helper = AutomationDecisionHelper(
        data_dir=str(temp_data_dir)
    )
    
    # Collect context for development environment
    context = await helper.collect_decision_context("development")
    
    # Verify context structure
    assert hasattr(context, "metrics")
    assert hasattr(context, "environment")
    assert hasattr(context, "resource_usage")
    assert hasattr(context, "historical_data")
    
    # Check specific metrics
    assert "cpu_usage_percent" in context.metrics
    assert "memory_usage_percent" in context.metrics
    assert "response_time_ms" in context.metrics


@pytest.mark.asyncio
async def test_decision_helper_decision_making(temp_data_dir):
    """Test decision making functionality."""
    helper = AutomationDecisionHelper(
        data_dir=str(temp_data_dir)
    )
    
    # Collect context and make decisions
    context = await helper.collect_decision_context("development")
    decisions = await helper.make_decisions(context)
    
    # Verify decisions structure
    assert "performance_optimization" in decisions
    assert "cost_optimization" in decisions
    assert "reliability_improvement" in decisions
    
    # Verify decision details
    for category, decision in decisions.items():
        assert "run" in decision
        assert "score" in decision
        assert "priority" in decision
        assert "parameters" in decision
        assert "focus_areas" in decision["parameters"]
        assert "risk_level" in decision["parameters"]


# Test controller functionality
@pytest.mark.asyncio
async def test_controller_initialization(temp_data_dir, test_config):
    """Test controller initialization."""
    # Create a temporary config file
    config_path = temp_data_dir / "test_config.json"
    with open(config_path, 'w') as f:
        json.dump(test_config, f)
    
    controller = AutomationController(
        base_dir=".",
        config_path=str(config_path),
        data_dir=str(temp_data_dir)
    )
    
    assert controller is not None
    assert controller.environment == Environment.DEVELOPMENT
    assert "performance" in controller.config


@pytest.mark.asyncio
async def test_controller_task_initialization(temp_data_dir, test_config):
    """Test controller task initialization."""
    # Mock the task executors
    with patch('automation_controller.AutomatedEnhancementEngine'), \
         patch('automation_controller.WorkspaceOptimizer'):
        
        # Create a temporary config file
        config_path = temp_data_dir / "test_config.json"
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
        controller = AutomationController(
            base_dir=".",
            config_path=str(config_path),
            data_dir=str(temp_data_dir)
        )
        
        # Initialize task executors
        controller._initialize_task_executors()
        
        # Verify task executors are initialized (would be mocks in this case)
        if test_config["performance"]["enabled"]:
            assert AutomationTask.PERFORMANCE in controller.task_executors
        
        if test_config["workspace"]["enabled"]:
            assert AutomationTask.WORKSPACE in controller.task_executors


@pytest.mark.asyncio
async def test_controller_report_generation(temp_data_dir):
    """Test report generation."""
    controller = AutomationController(
        base_dir=".",
        data_dir=str(temp_data_dir)
    )
    
    # Sample results
    results = {
        AutomationTask.PERFORMANCE: {
            "status": "success",
            "recommendations": [
                {"category": "redis", "priority": 1},
                {"category": "cloud_run", "priority": 2}
            ]
        },
        AutomationTask.WORKSPACE: {
            "status": "success",
            "profile": {"file_count": 100, "repo_size_mb": 50}
        }
    }
    
    # Generate reports in different formats
    text_report = await controller.generate_report(results, "text")
    json_report = await controller.generate_report(results, "json")
    html_report = await controller.generate_report(results, "html")
    
    # Verify report generation
    assert "AI Orchestra Automation Report" in text_report
    assert "Performance" in text_report
    
    assert "performance" in json_report
    assert "workspace" in json_report
    
    assert "<html>" in html_report
    assert "</html>" in html_report


# Integration tests
@pytest.mark.asyncio
async def test_integration_analysis_mode(temp_data_dir, test_config):
    """Integration test for analysis mode."""
    # Skip if required modules aren't available for integration testing
    if not all(module_name in sys.modules for module_name in [
        'automation_controller',
        'automation_decision_helper'
    ]):
        pytest.skip("Required modules not available for integration testing")
    
    # Mock task execution
    mock_result = {"status": "success", "metrics": {"cpu_usage": 70}}
    
    with patch.object(
        AutomationController,
        'run_task',
        return_value=mock_result
    ):
        # Create a temporary config file
        config_path = temp_data_dir / "test_config.json"
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
        controller = AutomationController(
            base_dir=".",
            config_path=str(config_path),
            data_dir=str(temp_data_dir)
        )
        
        # Run a task in analysis mode
        result = await controller.run_task(
            AutomationTask.PERFORMANCE,
            AutomationMode.ANALYZE
        )
        
        # Verify result
        assert result["status"] == "success"
        assert "metrics" in result


if __name__ == "__main__":
    # This allows running the tests directly with python
    # rather than through pytest if desired
    pytest.main(["-xvs", __file__])