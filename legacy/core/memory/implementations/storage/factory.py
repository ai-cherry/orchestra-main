# TODO: Consider adding connection pooling configuration
"""
"""
    """
    """
        """
        """
        logger.info(f"Registered {storage_class.__name__} for tier {tier.value}")
    
    @classmethod
    def create_storage(
        cls,
        tier: MemoryTier,
        config: MemoryConfig
    ) -> IMemoryStorage:
        """
        """
                config_section="storage_factory",
                parameter="tier",
                value=tier.value,
                reason=f"No storage implementation registered for tier {tier.value}"
            )
        
        storage_class = cls._storage_classes[tier]
        
        # Get tier-specific configuration
        tier_config = config.tiers.get(tier.value)
        if not tier_config or not tier_config.enabled:
            raise MemoryConfigurationError(
                config_section="storage_factory",
                parameter="tier_config",
                value=tier.value,
                reason=f"Tier {tier.value} is not enabled in configuration"
            )
        
        # Create storage instance with appropriate config
        logger.info(f"Creating {storage_class.__name__} for tier {tier.value}")
        
        try:

        
            pass
            if tier == MemoryTier.L0_CPU_CACHE:
                from shared.inmemory import InMemoryStorage
                return InMemoryStorage(
                    tier=tier,
                    max_size_bytes=tier_config.max_size_bytes,
                    max_items=tier_config.max_items,
                    eviction_policy=tier_config.eviction_policy
                )
                
            elif tier == MemoryTier.L1_PROCESS_MEMORY:
                from shared.inmemory import InMemoryStorage
                return InMemoryStorage(
                    tier=tier,
                    max_size_bytes=tier_config.max_size_bytes,
                    max_items=tier_config.max_items,
                    eviction_policy=tier_config.eviction_policy
                )
                
            elif tier == MemoryTier.L2_SHARED_MEMORY:
                from shared.shared import SharedMemoryStorage
                return SharedMemoryStorage(
                    tier=tier,
                    max_size_bytes=tier_config.max_size_bytes,
                    redis_config=config.redis
                )
                
            elif tier == MemoryTier.L3_POSTGRESQL:
                from shared.postgresql import PostgreSQLStorage
                return PostgreSQLStorage(
                    tier=tier,
                    config=config.postgresql,
                    table_name="memory_items"
                )
                
            elif tier == MemoryTier.L4_WEAVIATE:
                from shared.weaviate import WeaviateStorage
                return WeaviateStorage(
                    tier=tier,
                    config=config.weaviate
                )
                
            else:
                raise MemoryConfigurationError(
                    config_section="storage_factory",
                    parameter="tier",
                    value=tier.value,
                    reason=f"Unknown tier: {tier.value}"
                )
                
        except Exception:

                
            pass
            logger.error(f"Failed to create storage for tier {tier.value}: {str(e)}")
            raise MemoryConfigurationError(
                config_section="storage_factory",
                parameter="storage_creation",
                value=tier.value,
                reason=f"Failed to create storage: {str(e)}",
                cause=e
            )
    
    @classmethod
    def create_all_storages(
        cls,
        config: MemoryConfig
    ) -> Dict[MemoryTier, IMemoryStorage]:
        """
        """
                    logger.info(f"Created storage for tier {tier.value}")
                except Exception:

                    pass
                    logger.warning(
                        f"Failed to create storage for tier {tier.value}: {str(e)}"
                    )
                    # Continue with other tiers
        
        if not storages:
            raise MemoryConfigurationError(
                config_section="storage_factory",
                parameter="enabled_tiers",
                value="none",
                reason="No storage tiers are enabled in configuration"
            )
        
        return storages
    
    @classmethod
    def validate_storage_config(
        cls,
        tier: MemoryTier,
        config: MemoryConfig
    ) -> bool:
        """
        """
            logger.error(f"Configuration validation failed for tier {tier.value}: {str(e)}")
            return False

# Auto-registration of default storage implementations
def _register_default_storages():
    """Register default storage implementations."""
        logger.warning(f"Failed to register default storages: {str(e)}")

# Register defaults on module import
_register_default_storages()