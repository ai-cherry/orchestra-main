#!/usr/bin/env python3
"""
agent_mode_manager.py - Agent Mode Manager for MCP

This module provides a manager for agent modes, allowing registration, activation,
and management of different specialized AI assistant modes. It supports loading
configurations from files and provides a centralized interface for mode operations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Import from relative paths
from ..models.agent_mode import DEFAULT_AGENT_MODES, AgentMode, AgentModeConfig, AgentModeType
from ..utils.structured_logging import get_logger, with_correlation_id

logger = get_logger(__name__)

class AgentModeManager:
    """Manager for agent modes and their configurations."""

    def __init__(self, config_path: Optional[str] = None, auto_load_defaults: bool = True):
        """Initialize the agent mode manager.

        Args:
            config_path: Path to the agent mode configuration file (JSON or YAML)
            auto_load_defaults: Whether to automatically load default modes
        """
        self.modes: Dict[AgentModeType, AgentMode] = {}
        self.active_mode: Optional[AgentModeType] = None
        self.config_path = config_path
        self.last_loaded = None

        # Load default modes if requested
        if auto_load_defaults:
            self._register_default_modes()

        # Load from config file if provided
        if self.config_path:
            self.load_from_file(self.config_path)

    @with_correlation_id
    async def initialize(self) -> bool:
        """Initialize the agent mode manager asynchronously.

        Returns:
            bool: True if initialization was successful
        """
        logger.info("Initializing agent mode manager")

        try:
            # Load from config file if provided and not already loaded
            if self.config_path and not self.last_loaded:
                self.load_from_file(self.config_path)

            # Set default active mode if none is set
            if not self.active_mode and AgentModeType.DEFAULT in self.modes:
                self.set_active_mode(AgentModeType.DEFAULT)

            logger.info(f"Agent mode manager initialized with {len(self.modes)} modes")
            return True
        except Exception as e:
            logger.error(f"Error initializing agent mode manager: {e}")
            # Register defaults as fallback
            if not self.modes:
                self._register_default_modes()
            return False

    def _register_default_modes(self) -> None:
        """Register default agent modes."""
        for mode_type, config in DEFAULT_AGENT_MODES.items():
            self.register_mode(AgentMode(mode_type=mode_type, config=config))

        logger.info(f"Registered {len(DEFAULT_AGENT_MODES)} default agent modes")

    def load_from_file(self, file_path: str) -> bool:
        """Load agent mode configurations from a file.

        Args:
            file_path: Path to the configuration file (JSON or YAML)

        Returns:
            bool: True if loading was successful
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"Configuration file not found: {file_path}")
                return False

            # Load based on file extension
            if path.suffix.lower() in [".yaml", ".yml"]:
                with open(path, "r") as f:
                    config_data = yaml.safe_load(f)
            elif path.suffix.lower() == ".json":
                with open(path, "r") as f:
                    config_data = json.load(f)
            else:
                logger.error(f"Unsupported file format: {path.suffix}")
                return False

            # Process mode configurations
            modes_loaded = 0
            for mode_data in config_data.get("modes", []):
                try:
                    # Parse mode type
                    mode_type_str = mode_data.get("mode_type")
                    if not mode_type_str:
                        logger.warning("Mode type not specified, skipping")
                        continue

                    mode_type = AgentModeType(mode_type_str)

                    # Create config
                    config = AgentModeConfig(
                        name=mode_data.get("name", mode_type_str),
                        description=mode_data.get("description", ""),
                        system_prompt=mode_data.get("system_prompt", ""),
                        required_context=mode_data.get("required_context", []),
                        suggested_tools=mode_data.get("suggested_tools", []),
                        example_prompts=mode_data.get("example_prompts", []),
                        token_multiplier=mode_data.get("token_multiplier", 1.0),
                        constraints=mode_data.get("constraints", []),
                    )

                    # Register mode
                    self.register_mode(AgentMode(mode_type=mode_type, config=config))
                    modes_loaded += 1
                except Exception as e:
                    logger.error(f"Error loading mode configuration: {e}")

            self.last_loaded = datetime.now()
            logger.info(f"Loaded {modes_loaded} agent modes from {file_path}")
            return modes_loaded > 0
        except Exception as e:
            logger.error(f"Error loading agent mode configurations: {e}")
            return False

    def register_mode(self, mode: AgentMode) -> bool:
        """Register an agent mode.

        Args:
            mode: The agent mode to register

        Returns:
            bool: True if registration was successful
        """
        try:
            self.modes[mode.mode_type] = mode
            logger.info(f"Registered agent mode: {mode.config.name}")
            return True
        except Exception as e:
            logger.error(f"Error registering agent mode: {e}")
            return False

    def get_mode(self, mode_type: AgentModeType) -> Optional[AgentMode]:
        """Get an agent mode by type.

        Args:
            mode_type: The type of agent mode to get

        Returns:
            The agent mode, or None if not found
        """
        return self.modes.get(mode_type)

    def set_active_mode(self, mode_type: AgentModeType) -> bool:
        """Set the active agent mode.

        Args:
            mode_type: The type of agent mode to activate

        Returns:
            bool: True if activation was successful
        """
        if mode_type not in self.modes:
            logger.error(f"Agent mode not found: {mode_type}")
            return False

        # Deactivate current mode
        if self.active_mode:
            self.modes[self.active_mode].active = False

        # Activate new mode
        self.modes[mode_type].active = True
        self.active_mode = mode_type
        logger.info(f"Activated agent mode: {self.modes[mode_type].config.name}")
        return True

    def get_active_mode(self) -> Optional[AgentMode]:
        """Get the active agent mode.

        Returns:
            The active agent mode, or None if no mode is active
        """
        if not self.active_mode:
            return None
        return self.modes.get(self.active_mode)

    def get_all_modes(self) -> List[AgentMode]:
        """Get all registered agent modes.

        Returns:
            List of all registered agent modes
        """
        return list(self.modes.values())

    def get_mode_names(self) -> Dict[str, str]:
        """Get a mapping of mode types to their display names.

        Returns:
            Dictionary mapping mode types to display names
        """
        return {mode_type.value: mode.config.name for mode_type, mode in self.modes.items()}

    def format_prompt(self, task: str, context: Dict[str, Any] = None) -> str:
        """Format a prompt using the active agent mode.

        Args:
            task: The task to perform
            context: Optional context for the task

        Returns:
            The formatted prompt
        """
        active_mode = self.get_active_mode()
        if not active_mode:
            # Fall back to default mode
            if AgentModeType.DEFAULT in self.modes:
                active_mode = self.modes[AgentModeType.DEFAULT]
            else:
                # No modes available, return raw task
                return task

        return active_mode.format_prompt(task, context or {})

    def update_mode_context(self, mode_type: AgentModeType, context: Dict[str, Any]) -> bool:
        """Update the context for a specific mode.

        Args:
            mode_type: The type of agent mode to update
            context: The context to update

        Returns:
            bool: True if update was successful
        """
        mode = self.get_mode(mode_type)
        if not mode:
            logger.error(f"Agent mode not found: {mode_type}")
            return False

        # Update context (merge with existing)
        mode.context.update(context)
        logger.debug(f"Updated context for mode {mode.config.name}")
        return True

    def clear_mode_context(self, mode_type: AgentModeType) -> bool:
        """Clear the context for a specific mode.

        Args:
            mode_type: The type of agent mode to clear context for

        Returns:
            bool: True if clearing was successful
        """
        mode = self.get_mode(mode_type)
        if not mode:
            logger.error(f"Agent mode not found: {mode_type}")
            return False

        mode.context = {}
        logger.debug(f"Cleared context for mode {mode.config.name}")
        return True

    def save_to_file(self, file_path: str) -> bool:
        """Save agent mode configurations to a file.

        Args:
            file_path: Path to save the configuration file

        Returns:
            bool: True if saving was successful
        """
        try:
            # Convert modes to serializable format
            modes_data = []
            for mode in self.modes.values():
                mode_data = {
                    "mode_type": mode.mode_type.value,
                    "name": mode.config.name,
                    "description": mode.config.description,
                    "system_prompt": mode.config.system_prompt,
                    "required_context": mode.config.required_context,
                    "suggested_tools": mode.config.suggested_tools,
                    "example_prompts": mode.config.example_prompts,
                    "token_multiplier": mode.config.token_multiplier,
                    "constraints": mode.config.constraints,
                }
                modes_data.append(mode_data)

            config_data = {"modes": modes_data}

            # Save based on file extension
            path = Path(file_path)
            if path.suffix.lower() in [".yaml", ".yml"]:
                with open(path, "w") as f:
                    yaml.dump(config_data, f, default_flow_style=False)
            elif path.suffix.lower() == ".json":
                with open(path, "w") as f:
                    json.dump(config_data, f, indent=2)
            else:
                logger.error(f"Unsupported file format: {path.suffix}")
                return False

            logger.info(f"Saved {len(modes_data)} agent modes to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving agent mode configurations: {e}")
            return False

# Singleton instance for global use
_default_instance: Optional[AgentModeManager] = None

def get_agent_mode_manager() -> AgentModeManager:
    """Get the default AgentModeManager instance."""
    global _default_instance
    if _default_instance is None:
        _default_instance = AgentModeManager()
    return _default_instance

def get_active_mode() -> Optional[AgentMode]:
    """Convenience function to get the active agent mode."""
    return get_agent_mode_manager().get_active_mode()

def set_active_mode(mode_type: AgentModeType) -> bool:
    """Convenience function to set the active agent mode."""
    return get_agent_mode_manager().set_active_mode(mode_type)

def format_prompt(task: str, context: Dict[str, Any] = None) -> str:
    """Convenience function to format a prompt using the active agent mode."""
    return get_agent_mode_manager().format_prompt(task, context)
