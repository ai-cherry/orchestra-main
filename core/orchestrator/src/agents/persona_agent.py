"""
Persona-aware Agent Implementation for AI Orchestration System.

This module provides agent implementations that leverage persona information
to adapt their responses to match different interaction styles and traits.
"""

import logging
import random
from typing import Any, Dict, List, Optional

from core.orchestrator.src.agents.agent_base import Agent, AgentContext, AgentResponse

# Configure logging
logger = logging.getLogger(__name__)

class PersonaAwareAgent(Agent):
    agent_type = "simple_text"
    """
    Agent that adapts its response style based on persona traits.

    This agent specializes in crafting responses that mimic the style,
    tone, and personality traits defined in the persona configuration.
    It demonstrates how agents can be tailored to specific use cases.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a persona-aware agent.

        Args:
            config: Optional configuration for the agent
        """
        super().__init__(config)
        self.style_mappings = {
            "formal": self._formal_style,
            "casual": self._casual_style,
            "friendly": self._friendly_style,
            "technical": self._technical_style,
            "concise": self._concise_style,
            "elaborate": self._elaborate_style,
            "empathetic": self._empathetic_style,
            "witty": self._witty_style,
            "professional": self._professional_style,
        }

        # Response templates for different traits
        self.response_templates = {
            "helpful": [
                "I'd be happy to help with that. {response}",
                "I can definitely assist you. {response}",
                "Let me help you with that. {response}",
            ],
            "creative": [
                "Here's a creative approach: {response}",
                "Thinking outside the box: {response}",
                "Here's an interesting perspective on that: {response}",
            ],
            "technical": [
                "From a technical standpoint: {response}",
                "Looking at this technically: {response}",
                "Analyzing this systematically: {response}",
            ],
            "empathetic": [
                "I understand how you feel. {response}",
                "I can see why this matters to you. {response}",
                "That's a valid concern, and here's my thought: {response}",
            ],
            "analytical": [
                "Analyzing your request: {response}",
                "Let me break this down: {response}",
                "From an analytical perspective: {response}",
            ],
            "concise": ["In brief: {response}", "Simply put: {response}", "{response}"],
            "enthusiastic": [
                "I'm excited to share that {response}",
                "Great question! {response}",
                "I love discussing this! {response}",
            ],
            "cautious": [
                "I'd suggest considering that {response}",
                "It might be worth noting that {response}",
                "One thing to keep in mind: {response}",
            ],
        }

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process user input and generate a persona-aware response.

        This method generates responses that align with the persona's
        traits and interaction style, creating a more personalized experience.

        Args:
            context: The context for this interaction

        Returns:
            A personalized response based on the persona
        """
        user_input = context.user_input
        persona = context.persona

        # Analyze input to determine appropriate response content
        base_response = self._generate_base_response(user_input, persona)

        # Apply persona-specific styling
        persona_traits = persona.traits or ["helpful"]
        interaction_style = persona.interaction_style or "formal"

        # Style the response based on the persona's interaction style
        styled_response = self._apply_interaction_style(base_response, interaction_style)

        # Apply trait-specific templates
        final_response = self._apply_trait_template(styled_response, persona_traits)

        # Add persona-specific nuances
        if persona.name:
            # Sometimes reference the persona's name
            if random.random() < 0.2:  # 20% chance
                final_response = f"As {persona.name}, {final_response.lower()}"

        # Generate metadata about how the response was personalized
        metadata = {
            "persona_traits_used": persona_traits[:3],
            "interaction_style": interaction_style,
            "agent_type": "PersonaAwareAgent",
            "personalization_level": "high",
        }

        return AgentResponse(text=final_response, confidence=0.9, metadata=metadata)

    def can_handle(self, context: AgentContext) -> float:
        """
        Determine if this agent can handle the given context.

        This agent specializes in persona-aware responses and can handle
        most general conversation situations.

        Args:
            context: The context for this interaction

        Returns:
            A score between 0 and 1
        """
        # This agent is well-suited for conversations with defined personas
        persona = context.persona

        # Higher score if the persona has well-defined traits
        if persona.traits and len(persona.traits) >= 2:
            return 0.85

        # Still decent score for less defined personas
        return 0.75

    def _generate_base_response(self, user_input: str, persona: Any) -> str:
        """
        Generate the base response content.

        In a real implementation, this would leverage an LLM to generate
        appropriate content based on the user input and persona context.

        Args:
            user_input: The user's input message
            persona: The selected persona

        Returns:
            The base response text
        """
        # For demonstration, create a simple response
        # In a real implementation, this would call an LLM

        # Extract topic from user input (simplified)
        topic = user_input.split()[-1] if user_input.split() else "that"

        # Generate appropriate responses based on persona expertise
        expertise = persona.background or "general knowledge"

        if "tech" in expertise.lower() or "software" in expertise.lower():
            response = f"Based on my technical background, I can share insights about {topic}."
        elif "creative" in expertise.lower() or "art" in expertise.lower():
            response = f"From a creative perspective, there are many interesting aspects to {topic}."
        elif "business" in expertise.lower() or "finance" in expertise.lower():
            response = f"Looking at {topic} from a business standpoint, there are several factors to consider."
        else:
            response = f"I have some thoughts about {topic} that might be helpful."

        return response

    def _apply_interaction_style(self, text: str, style: str) -> str:
        """
        Apply a specific interaction style to the text.

        Args:
            text: The base text to style
            style: The interaction style to apply

        Returns:
            The styled text
        """
        # Use the appropriate styling function based on style
        style_func = self.style_mappings.get(style.lower(), self._formal_style)
        return style_func(text)

    def _apply_trait_template(self, text: str, traits: List[str]) -> str:
        """
        Apply a trait-specific template to the response.

        Args:
            text: The styled response text
            traits: List of persona traits

        Returns:
            The response with trait-specific template applied
        """
        # Select a relevant trait that we have templates for
        available_traits = [t for t in traits if t.lower() in self.response_templates]

        if not available_traits:
            # Default to helpful if no matching traits
            trait = "helpful"
        else:
            # Randomly select one of the matching traits
            trait = random.choice(available_traits).lower()

        # Select a random template for the trait
        templates = self.response_templates.get(trait, self.response_templates["helpful"])
        template = random.choice(templates)

        # Apply the template
        return template.format(response=text)

    # Style transformation functions

    def _formal_style(self, text: str) -> str:
        """Apply a formal style to text."""
        # In a real implementation, this would use more sophisticated NLP
        return text.replace("I can ", "I am able to ").replace("can't", "cannot")

    def _casual_style(self, text: str) -> str:
        """Apply a casual style to text."""
        return text.replace("I am", "I'm").replace("will not", "won't")

    def _friendly_style(self, text: str) -> str:
        """Apply a friendly style to text."""
        return f"{text} I hope that helps!"

    def _technical_style(self, text: str) -> str:
        """Apply a technical style to text."""
        return f"Technically speaking, {text}"

    def _concise_style(self, text: str) -> str:
        """Apply a concise style to text."""
        # Simplistic implementation - would be more sophisticated in real system
        return text.split(". ")[0] + "."

    def _elaborate_style(self, text: str) -> str:
        """Apply an elaborate style to text."""
        return f"{text} There are, of course, multiple facets to consider here."

    def _empathetic_style(self, text: str) -> str:
        """Apply an empathetic style to text."""
        return f"I understand your interest in this. {text}"

    def _witty_style(self, text: str) -> str:
        """Apply a witty style to text."""
        return f"{text} Who would have thought, right?"

    def _professional_style(self, text: str) -> str:
        """Apply a professional style to text."""
        return f"From a professional standpoint, {text}"

class DomainSpecificAgent(PersonaAwareAgent):
    """
    Agent specializing in a specific knowledge domain.

    This agent extends the PersonaAwareAgent with additional capabilities
    for handling domain-specific queries. It demonstrates how the agent
    framework can be extended for specialized applications.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a domain-specific agent.

        Args:
            config: Optional configuration for the agent
        """
        super().__init__(config)
        self.domain = config.get("domain", "general") if config else "general"

        # Domain-specific knowledge repositories would be integrated here
        self.domain_knowledge = {
            "tech": ["software", "hardware", "programming", "ai", "web"],
            "business": ["finance", "marketing", "management", "strategy"],
            "science": ["physics", "biology", "chemistry", "research"],
            "health": ["medicine", "wellness", "fitness", "nutrition"],
        }

        logger.info(f"DomainSpecificAgent initialized for domain: {self.domain}")

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process user input with domain-specific knowledge.

        Args:
            context: The context for this interaction

        Returns:
            A domain-informed response
        """
        # First, apply persona-aware processing
        base_response = await super().process(context)

        # Then enhance with domain-specific information
        if self.domain != "general":
            # In a real implementation, this would access domain-specific
            # knowledge bases, APIs, or specialized models
            domain_addition = (
                f" In the {self.domain} domain, we often consider additional factors specific to this field."
            )

            # Update the response
            enhanced_text = f"{base_response.text} {domain_addition}"
            enhanced_metadata = {
                **base_response.metadata,
                "domain": self.domain,
                "domain_confidence": 0.95,
                "agent_type": "DomainSpecificAgent",
            }

            return AgentResponse(
                text=enhanced_text,
                confidence=base_response.confidence * 1.05,  # Slight boost
                metadata=enhanced_metadata,
            )

        return base_response

    def can_handle(self, context: AgentContext) -> float:
        """
        Determine if this agent can handle the given context.

        Args:
            context: The context for this interaction

        Returns:
            A score between 0 and 1
        """
        # Get base score from parent class
        base_score = super().can_handle(context)

        # Check if the input relates to our domain
        domain_relevance = self._calculate_domain_relevance(context.user_input)

        # Combine scores, with domain relevance having a significant impact
        return 0.4 * base_score + 0.6 * domain_relevance

    def _calculate_domain_relevance(self, text: str) -> float:
        """
        Calculate how relevant the input is to this agent's domain.

        Args:
            text: The input text to evaluate

        Returns:
            A score between 0 and 1
        """
        # Simple keyword-based relevance for demonstration
        # In a real implementation, this would use more sophisticated
        # NLP techniques like embeddings or topic modeling

        text_lower = text.lower()
        keywords = self.domain_knowledge.get(self.domain, [])

        # Count domain-specific keywords in the input
        matches = sum(1 for keyword in keywords if keyword in text_lower)

        if not keywords:
            return 0.5  # Neutral for general domain

        # Calculate relevance score based on keyword matches
        relevance = min(1.0, matches / max(1, len(keywords) * 0.3))

        return relevance

# Factory function to create specialized agents
def create_specialized_agent(agent_type: str, config: Optional[Dict[str, Any]] = None) -> Agent:
    """
    Create a specialized agent based on type and configuration.

    Args:
        agent_type: The type of specialized agent to create
        config: Optional configuration for the agent

    Returns:
        An instantiated specialized agent

    Raises:
        ValueError: If the agent type is unknown
    """
    config = config or {}

    if agent_type == "persona_aware":
        return PersonaAwareAgent(config)
    elif agent_type == "domain_specific":
        return DomainSpecificAgent(config)
    else:
        raise ValueError(f"Unknown specialized agent type: {agent_type}")
