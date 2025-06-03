"""
"""
    """
    """
        auto_reload = settings.ENVIRONMENT == "development"
        cache_ttl = settings.CACHE_TTL_SECONDS

        logger.info(f"Initializing PersonaManager with config path: {config_path}")
        manager = PersonaManager(
            config_path=config_path,
            auto_reload=auto_reload,
            cache_ttl_seconds=cache_ttl,
        )

        return manager
    except Exception:

        pass
        logger.error(f"Failed to initialize PersonaManager: {e}")
        # Return a default manager as fallback
        logger.warning("Falling back to default PersonaManager")
        return PersonaManager()

def get_persona_by_id(persona_id: Optional[str] = None):
    """
    """