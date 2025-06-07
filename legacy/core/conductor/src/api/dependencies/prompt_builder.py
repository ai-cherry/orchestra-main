"""
"""
    """
    """
    return PromptBuilder()

def build_prompt_for_persona(
    persona: PersonaConfig,
    user_input: str,
    history_items: Optional[list[MemoryItem]] = None,
    additional_context: Optional[Dict[str, Any]] = None,
    builder: PromptBuilder = Depends(get_prompt_builder),
) -> list[Dict[str, str]]:
    """
    """

    # Use PromptBuilder to create a prompt
    prompt = builder.build_prompt(
        persona=persona,
        user_input=user_input,
        history_items=history_items,
        format=PromptFormat.CHAT,
        additional_context=additional_context,
    )

    return prompt
