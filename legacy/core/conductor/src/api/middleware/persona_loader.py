"""
"""
    """
    """
    """
    """
    """
    """
    # Get persona name from query parameters, default to "cherry"
    persona_name = request.query_params.get("persona", "cherry")

    # Try to get the requested persona
    active_persona = persona_configs.get(persona_name)

    # If requested persona doesn't exist, try to use "cherry" as fallback
    if not active_persona and persona_name != "cherry":
        logger.warning(f"Persona '{persona_name}' not found, falling back to 'cherry'")
        active_persona = persona_configs.get("cherry")

    # If cherry is also missing, create an emergency persona
    if not active_persona:
        logger.error("No valid persona found, creating emergency fallback persona")
        # Create an emergency fallback persona
        active_persona = PersonaConfig(
            name="Emergency Assistant",
            description="Emergency fallback assistant",
            prompt_template="You are an emergency fallback assistant. The system encountered an issue loading the requested persona. Please assist the user while notifying them of this issue.",
            traits={"helpfulness": 0.9, "reliability": 0.9},
            metadata={"emergency_fallback": True},
        )

        # Try to reload personas in case it's a temporary issue
        try:

            pass
            logger.info("Attempting to reload personas")
            refreshed_configs = reload_personas()
            # Check if we now have the requested persona or at least cherry
            if persona_name in refreshed_configs:
                active_persona = refreshed_configs[persona_name]
                logger.info(f"Successfully loaded '{persona_name}' on reload")
            elif "cherry" in refreshed_configs:
                active_persona = refreshed_configs["cherry"]
                logger.info("Successfully loaded 'cherry' as fallback on reload")
        except Exception:

            pass
            logger.error(f"Failed to reload personas: {e}")

    # Track which persona was actually used
    request.state.requested_persona = persona_name
    request.state.active_persona = active_persona

    # Log persona selection result
    if persona_name != active_persona.name.lower():
        logger.info(f"Using '{active_persona.name}' instead of requested '{persona_name}'")
    else:

    return active_persona
