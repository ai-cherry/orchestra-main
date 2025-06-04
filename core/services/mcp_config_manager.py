import os
import yaml
import logging
import asyncio
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import pydantic # For ValidationError

from core.models.mcp_instance_models import UserDefinedMCPServerInstanceConfig

logger = logging.getLogger(__name__)

class MCPConfigManager:
    def __init__(self, config_filepath: str = "config/mcp_servers.yaml"):
        self.config_filepath = config_filepath
        self._lock = asyncio.Lock()
        # Ensure the directory for the config file exists on initialization
        try:
            os.makedirs(os.path.dirname(self.config_filepath), exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory for config file {self.config_filepath}: {e}")


    def _load_all_configs_from_file(self) -> List[UserDefinedMCPServerInstanceConfig]:
        if not os.path.exists(self.config_filepath):
            logger.info(f"Config file {self.config_filepath} not found. Returning empty list.")
            return []

        try:
            with open(self.config_filepath, 'r') as f:
                # Handle empty file case
                content = f.read()
                if not content.strip():
                    logger.info(f"Config file {self.config_filepath} is empty. Returning empty list.")
                    return []
                # Reset cursor to beginning for yaml.safe_load
                f.seek(0)
                configs_data = yaml.safe_load(content)

            if not configs_data: # Handles cases like file containing only "[]" or "-"
                return []

            configs = [UserDefinedMCPServerInstanceConfig(**data) for data in configs_data]
            return configs
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML from {self.config_filepath}: {e}")
            return [] # Or raise an exception / handle more gracefully
        except pydantic.ValidationError as e:
            logger.error(f"Validation error loading configs from {self.config_filepath}: {e}")
            return [] # Or raise
        except Exception as e:
            logger.error(f"Unexpected error loading configs from {self.config_filepath}: {e}", exc_info=True)
            return []


    def _write_all_configs_to_file(self, configs: List[UserDefinedMCPServerInstanceConfig]):
        try:
            # Ensure parent directory exists (useful if path is dynamic or created at runtime)
            os.makedirs(os.path.dirname(self.config_filepath), exist_ok=True)

            # For Pydantic v2, use model_dump(). For v1, dict() is common.
            # Assuming Pydantic v2 for model_dump, adjust if using v1.
            configs_data = [c.model_dump(mode='json') for c in configs] # mode='json' helps with datetime/UUID

            with open(self.config_filepath, 'w') as f:
                yaml.dump(configs_data, f, sort_keys=False, default_flow_style=False)
            logger.debug(f"Successfully wrote {len(configs)} configs to {self.config_filepath}")
        except IOError as e:
            logger.error(f"IOError writing configs to {self.config_filepath}: {e}")
        except yaml.YAMLError as e:
            logger.error(f"Error serializing configs to YAML for {self.config_filepath}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error writing configs to {self.config_filepath}: {e}", exc_info=True)

    async def get_all_configs(self) -> List[UserDefinedMCPServerInstanceConfig]:
        async with self._lock:
            return self._load_all_configs_from_file()

    async def get_config_by_id(self, server_id: UUID) -> Optional[UserDefinedMCPServerInstanceConfig]:
        async with self._lock:
            configs = self._load_all_configs_from_file()
            for config in configs:
                if config.id == server_id:
                    return config
            return None

    def _generate_internal_mcp_config_yaml_str(self, user_config: UserDefinedMCPServerInstanceConfig) -> str:
        internal_config_dict: Dict[str, Any] = {
            "storage": {"type": "in_memory", "max_entries": 10000, "ttl_seconds": 86400},
            "debug": False,
            "log_level": "INFO",
            "port": 9000, # Default, matching Dockerfile healthcheck
            "host": "0.0.0.0",
            "servers": {}, # Default empty dict
        }

        if "copilot" in user_config.enabled_internal_tools:
            internal_config_dict["copilot"] = {"enabled": True, "api_key": None} # API key explicitly None
            if user_config.copilot_config_override:
                # Merge overrides carefully, ensuring 'enabled' and 'api_key' are not improperly changed
                # A more sophisticated merge might be needed if overrides can unset 'enabled'
                temp_override = user_config.copilot_config_override.copy()
                temp_override.pop("api_key", None) # Ensure api_key override is ignored
                internal_config_dict["copilot"].update(temp_override)

        if "gemini" in user_config.enabled_internal_tools:
            internal_config_dict["gemini"] = {"enabled": True, "api_key": None} # API key explicitly None
            if user_config.gemini_config_override:
                temp_override = user_config.gemini_config_override.copy()
                temp_override.pop("api_key", None)
                internal_config_dict["gemini"].update(temp_override)

        # TODO: Add similar blocks for other potential internal tools as MCPConfig model evolves
        # e.g., claude_internal_config_override, openai_internal_config_override

        try:
            return yaml.dump(internal_config_dict, sort_keys=False, default_flow_style=False)
        except yaml.YAMLError as e:
            logger.error(f"Error generating internal MCPConfig YAML for {user_config.name}: {e}")
            return "" # Return empty or error string

    async def save_config(self, config_data: UserDefinedMCPServerInstanceConfig) -> UserDefinedMCPServerInstanceConfig:
        async with self._lock:
            configs = self._load_all_configs_from_file()

            config_data.updated_at = datetime.utcnow()

            # Generate the internal config YAML string
            try:
                config_data.generated_mcp_internal_config_yaml = self._generate_internal_mcp_config_yaml_str(config_data)
            except Exception as e: # Catch any error during generation
                logger.error(f"Failed to generate internal MCP config for {config_data.name}: {e}", exc_info=True)
                # Decide on error handling: raise, or save with None/empty YAML, or return error
                # For now, proceeding to save with potentially missing generated_mcp_internal_config_yaml

            found_idx = -1
            if config_data.id: # If ID is present, try to find and update
                for i, existing_config in enumerate(configs):
                    if existing_config.id == config_data.id:
                        found_idx = i
                        break

            if found_idx != -1: # Update existing
                # Preserve created_at from original, only update updated_at
                config_data.created_at = configs[found_idx].created_at
                configs[found_idx] = config_data
                logger.info(f"Updated MCP server config for ID: {config_data.id}")
            else: # Create new
                if not config_data.id: # Assign new ID if not provided (e.g. for brand new entries)
                    config_data.id = uuid4()
                config_data.created_at = datetime.utcnow() # Set created_at for new entries
                configs.append(config_data)
                logger.info(f"Created new MCP server config for ID: {config_data.id} with name: {config_data.name}")

            self._write_all_configs_to_file(configs)
            return config_data

    async def delete_config(self, server_id: UUID) -> bool:
        async with self._lock:
            configs = self._load_all_configs_from_file()
            initial_len = len(configs)
            configs = [c for c in configs if c.id != server_id]

            if len(configs) < initial_len:
                self._write_all_configs_to_file(configs)
                logger.info(f"Deleted MCP server config with ID: {server_id}")
                return True
            else:
                logger.warning(f"Attempted to delete non-existent MCP server config with ID: {server_id}")
                return False
