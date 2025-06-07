"""
"""
    """
    """
    logger.info(f"Instantiating agent: {agent_name}")

    # Use a simple if/elif structure to map agent names to their implementations
    if agent_name == "web_scraper":
        logger.info("Creating WebScraperRuntimeAgent instance")
        return WebScraperRuntimeAgent(config=config, persona=persona, memory_manager=memory_manager)

    # If we get here, no matching agent was found
    logger.warning(f"No agent implementation found for: {agent_name}")
    raise ValueError(f"Unknown agent type: {agent_name}")
