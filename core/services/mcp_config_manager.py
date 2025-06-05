import os
import yaml
import logging
import asyncio
import hashlib
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import pydantic # For ValidationError

from core.models.mcp_instance_models import UserDefinedMCPServerInstanceConfig
from core.utils.performance import cached, performance_monitor, SimpleCache

logger = logging.getLogger(__name__)

class OptimizedMCPConfigManager:
    """
    Performance-optimized MCP Configuration Manager
    Features:
    - In-memory caching with TTL
    - Performance monitoring
    - Batch operations
    - File change detection
    - Async optimization
    """
    
    def __init__(self, config_filepath: str = "config/mcp_servers.yaml"):
        self.config_filepath = config_filepath
        self._lock = asyncio.Lock()
        self._cache = SimpleCache(default_ttl=300)  # 5-minute cache
        self._file_hash = None
        self._last_load_time = None
        
        # Ensure the directory for the config file exists on initialization
        try:
            os.makedirs(os.path.dirname(self.config_filepath), exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory for config file {self.config_filepath}: {e}")

    def _get_file_hash(self) -> Optional[str]:
        """Get hash of config file for change detection"""
        try:
            if not os.path.exists(self.config_filepath):
                return None
            
            with open(self.config_filepath, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return None

    def _has_file_changed(self) -> bool:
        """Check if config file has changed since last load"""
        current_hash = self._get_file_hash()
        if current_hash != self._file_hash:
            self._file_hash = current_hash
            return True
        return False

    @performance_monitor("load_configs_from_file")
    def _load_all_configs_from_file(self) -> List[UserDefinedMCPServerInstanceConfig]:
        """Load configurations with performance monitoring and caching"""
        
        # Check cache first if file hasn't changed
        if not self._has_file_changed() and self._last_load_time:
            cached_configs = self._cache.get("all_configs")
            if cached_configs is not None:
                logger.debug("Returning cached configurations")
                return cached_configs

        if not os.path.exists(self.config_filepath):
            logger.info(f"Config file {self.config_filepath} not found. Returning empty list.")
            configs = []
        else:
            try:
                with open(self.config_filepath, 'r') as f:
                    content = f.read()
                    if not content.strip():
                        logger.info(f"Config file {self.config_filepath} is empty. Returning empty list.")
                        configs = []
                    else:
                        configs_data = yaml.safe_load(content)
                        if not configs_data:
                            configs = []
                        else:
                            configs = [UserDefinedMCPServerInstanceConfig(**data) for data in configs_data]
                            
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML from {self.config_filepath}: {e}")
                configs = []
            except pydantic.ValidationError as e:
                logger.error(f"Validation error loading configs from {self.config_filepath}: {e}")
                configs = []
            except Exception as e:
                logger.error(f"Unexpected error loading configs from {self.config_filepath}: {e}", exc_info=True)
                configs = []

        # Cache the results
        self._cache.set("all_configs", configs, ttl=300)
        self._last_load_time = datetime.now()
        
        # Also cache individual configs by ID for faster lookups
        for config in configs:
            self._cache.set(f"config_by_id:{config.id}", config, ttl=300)
        
        logger.debug(f"Loaded {len(configs)} configurations from file")
        return configs

    @performance_monitor("write_configs_to_file")
    def _write_all_configs_to_file(self, configs: List[UserDefinedMCPServerInstanceConfig]):
        """Write configurations with performance monitoring and cache invalidation"""
        try:
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(self.config_filepath), exist_ok=True)

            # Convert to serializable format
            configs_data = [c.model_dump(mode='json') for c in configs]

            # Write atomically using temporary file
            temp_filepath = f"{self.config_filepath}.tmp"
            with open(temp_filepath, 'w') as f:
                yaml.dump(configs_data, f, sort_keys=False, default_flow_style=False)
            
            # Atomic move
            os.replace(temp_filepath, self.config_filepath)
            
            # Invalidate cache
            self._cache.clear()
            self._file_hash = self._get_file_hash()
            
            logger.debug(f"Successfully wrote {len(configs)} configs to {self.config_filepath}")
            
        except IOError as e:
            logger.error(f"IOError writing configs to {self.config_filepath}: {e}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error serializing configs to YAML for {self.config_filepath}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error writing configs to {self.config_filepath}: {e}", exc_info=True)
            raise

    @performance_monitor("get_all_configs")
    async def get_all_configs(self) -> List[UserDefinedMCPServerInstanceConfig]:
        """Get all configurations with async optimization"""
        async with self._lock:
            return self._load_all_configs_from_file()

    @performance_monitor("get_config_by_id")
    async def get_config_by_id(self, server_id: UUID) -> Optional[UserDefinedMCPServerInstanceConfig]:
        """Get configuration by ID with caching optimization"""
        
        # Try cache first
        cached_config = self._cache.get(f"config_by_id:{server_id}")
        if cached_config is not None:
            logger.debug(f"Cache hit for config ID: {server_id}")
            return cached_config
        
        async with self._lock:
            configs = self._load_all_configs_from_file()
            for config in configs:
                if config.id == server_id:
                    # Cache the found config
                    self._cache.set(f"config_by_id:{server_id}", config, ttl=300)
                    return config
            return None

    @cached(ttl=60, key_func=lambda self, user_config: f"internal_config:{user_config.id}")
    def _generate_internal_mcp_config_yaml_str(self, user_config: UserDefinedMCPServerInstanceConfig) -> str:
        """Generate internal config with caching for expensive YAML operations"""
        internal_config_dict: Dict[str, Any] = {
            "storage": {"type": "in_memory", "max_entries": 10000, "ttl_seconds": 86400},
            "debug": False,
            "log_level": "INFO",
            "port": 9000,
            "host": "0.0.0.0",
            "servers": {},
        }

        if "copilot" in user_config.enabled_internal_tools:
            internal_config_dict["copilot"] = {"enabled": True, "api_key": None}
            if user_config.copilot_config_override:
                temp_override = user_config.copilot_config_override.copy()
                temp_override.pop("api_key", None)
                internal_config_dict["copilot"].update(temp_override)

        if "gemini" in user_config.enabled_internal_tools:
            internal_config_dict["gemini"] = {"enabled": True, "api_key": None}
            if user_config.gemini_config_override:
                temp_override = user_config.gemini_config_override.copy()
                temp_override.pop("api_key", None)
                internal_config_dict["gemini"].update(temp_override)

        try:
            return yaml.dump(internal_config_dict, sort_keys=False, default_flow_style=False)
        except yaml.YAMLError as e:
            logger.error(f"Error generating internal MCPConfig YAML for {user_config.name}: {e}")
            return ""

    @performance_monitor("save_config")
    async def save_config(self, config_data: UserDefinedMCPServerInstanceConfig) -> UserDefinedMCPServerInstanceConfig:
        """Save configuration with optimized performance"""
        async with self._lock:
            configs = self._load_all_configs_from_file()

            config_data.updated_at = datetime.utcnow()

            # Generate the internal config YAML string with caching
            try:
                config_data.generated_mcp_internal_config_yaml = self._generate_internal_mcp_config_yaml_str(config_data)
            except Exception as e:
                logger.error(f"Failed to generate internal MCP config for {config_data.name}: {e}", exc_info=True)
                # Continue with save but log the error

            found_idx = -1
            if config_data.id:
                for i, existing_config in enumerate(configs):
                    if existing_config.id == config_data.id:
                        found_idx = i
                        break

            if found_idx != -1:  # Update existing
                config_data.created_at = configs[found_idx].created_at
                configs[found_idx] = config_data
                logger.info(f"Updated MCP server config for ID: {config_data.id}")
            else:  # Create new
                if not config_data.id:
                    config_data.id = uuid4()
                config_data.created_at = datetime.utcnow()
                configs.append(config_data)
                logger.info(f"Created new MCP server config for ID: {config_data.id} with name: {config_data.name}")

            self._write_all_configs_to_file(configs)
            
            # Update cache
            self._cache.set(f"config_by_id:{config_data.id}", config_data, ttl=300)
            
            return config_data

    @performance_monitor("delete_config")
    async def delete_config(self, server_id: UUID) -> bool:
        """Delete configuration with cache invalidation"""
        async with self._lock:
            configs = self._load_all_configs_from_file()
            initial_len = len(configs)
            configs = [c for c in configs if c.id != server_id]

            if len(configs) < initial_len:
                self._write_all_configs_to_file(configs)
                
                # Invalidate specific cache entry
                self._cache.invalidate(f"config_by_id:{server_id}")
                
                logger.info(f"Deleted MCP server config with ID: {server_id}")
                return True
            else:
                logger.warning(f"Attempted to delete non-existent MCP server config with ID: {server_id}")
                return False

    async def bulk_save_configs(
        self,
        configs: List[UserDefinedMCPServerInstanceConfig]
    ) -> List[UserDefinedMCPServerInstanceConfig]:
        """Bulk save operation for better performance"""
        async with self._lock:
            existing_configs = self._load_all_configs_from_file()
            existing_by_id = {c.id: i for i, c in enumerate(existing_configs)}
            
            updated_configs = []
            
            for config_data in configs:
                config_data.updated_at = datetime.utcnow()
                
                # Generate internal config
                try:
                    config_data.generated_mcp_internal_config_yaml = self._generate_internal_mcp_config_yaml_str(config_data)
                except Exception as e:
                    logger.error(f"Failed to generate internal MCP config for {config_data.name}: {e}")
                
                if config_data.id and config_data.id in existing_by_id:
                    # Update existing
                    idx = existing_by_id[config_data.id]
                    config_data.created_at = existing_configs[idx].created_at
                    existing_configs[idx] = config_data
                else:
                    # Create new
                    if not config_data.id:
                        config_data.id = uuid4()
                    config_data.created_at = datetime.utcnow()
                    existing_configs.append(config_data)
                
                updated_configs.append(config_data)
            
            self._write_all_configs_to_file(existing_configs)
            
            # Update cache for all modified configs
            for config in updated_configs:
                self._cache.set(f"config_by_id:{config.id}", config, ttl=300)
            
            logger.info(f"Bulk saved {len(updated_configs)} configurations")
            return updated_configs

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        return self._cache.stats()

    def clear_cache(self) -> None:
        """Clear all cached data"""
        self._cache.clear()
        logger.info("Configuration cache cleared")

    async def validate_all_configs(self) -> Dict[str, Any]:
        """Validate all configurations and return validation report"""
        configs = await self.get_all_configs()
        
        validation_report = {
            "total_configs": len(configs),
            "valid_configs": 0,
            "invalid_configs": 0,
            "errors": []
        }
        
        for config in configs:
            try:
                # Re-validate the config
                UserDefinedMCPServerInstanceConfig(**config.model_dump())
                validation_report["valid_configs"] += 1
            except Exception as e:
                validation_report["invalid_configs"] += 1
                validation_report["errors"].append({
                    "config_id": str(config.id),
                    "config_name": config.name,
                    "error": str(e)
                })
        
        return validation_report


# Backward compatibility - alias to the original class name
MCPConfigManager = OptimizedMCPConfigManager

