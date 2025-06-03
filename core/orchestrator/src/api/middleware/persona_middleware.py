"""
"""
    """
    """
        """
        """
        persona_name = request.query_params.get("persona")

        try:


            pass
            # Get persona configuration
            persona_config = get_persona_config(request, persona_name)

            # Set on the request state
            request.state.active_persona = persona_config

        except Exception:

            pass
            # Log error but continue processing
            logger.error(f"Failed to set active persona: {e}")

        # Proceed with the request
        response = await call_next(request)
        return response
