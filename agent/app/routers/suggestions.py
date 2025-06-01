"""Search suggestions API endpoints for OmniSearch functionality."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from agent.app.routers.admin import verify_api_key

router = APIRouter(prefix="/api", tags=["suggestions"])


class Suggestion(BaseModel):
    """Individual suggestion model."""
    text: str
    type: str
    description: Optional[str] = None
    metadata: Optional[dict] = None
    score: Optional[float] = None


class SuggestionsResponse(BaseModel):
    """Response model for suggestions."""
    suggestions: List[Suggestion]


class SuggestionEngine:
    """Simple suggestion engine for MVP.
    
    In production, this would use ML models and user history for personalization.
    """
    
    # Static suggestions for different contexts
    SUGGESTIONS = {
        'agent_creation': [
            Suggestion(
                text="Create a data analysis agent",
                type="agent_creation",
                description="Build an agent that can analyze and visualize data",
                score=0.95
            ),
            Suggestion(
                text="Create a monitoring agent",
                type="agent_creation",
                description="Set up an agent to monitor system health",
                score=0.90
            ),
            Suggestion(
                text="Create a content generation agent",
                type="agent_creation",
                description="Design an agent for creating content",
                score=0.85
            ),
        ],
        'workflow': [
            Suggestion(
                text="Build data processing pipeline",
                type="workflow",
                description="Create a workflow for ETL operations",
                score=0.92
            ),
            Suggestion(
                text="Create notification workflow",
                type="workflow",
                description="Set up automated notifications and alerts",
                score=0.88
            ),
        ],
        'search': [
            Suggestion(
                text="Search recent agent activities",
                type="search",
                description="View what your agents have been doing",
                score=0.90
            ),
            Suggestion(
                text="Find workflow templates",
                type="search",
                description="Browse available workflow templates",
                score=0.85
            ),
        ],
        'generate': [
            Suggestion(
                text="Generate weekly report",
                type="generate",
                description="Create a summary of this week's activities",
                score=0.93
            ),
            Suggestion(
                text="Generate API documentation",
                type="generate",
                description="Auto-generate docs for your APIs",
                score=0.87
            ),
        ],
    }
    
    async def get_suggestions(
        self, 
        query: str, 
        mode: str = 'auto',
        limit: int = 10
    ) -> List[Suggestion]:
        """Get suggestions based on partial query."""
        query_lower = query.lower().strip()
        suggestions = []
        
        # Determine which suggestion categories to search
        if mode == 'auto':
            # Check query to determine likely intent
            if any(word in query_lower for word in ['create', 'build', 'new', 'agent']):
                categories = ['agent_creation', 'workflow']
            elif any(word in query_lower for word in ['search', 'find', 'show']):
                categories = ['search']
            elif any(word in query_lower for word in ['generate', 'write', 'create']):
                categories = ['generate']
            else:
                categories = list(self.SUGGESTIONS.keys())
        else:
            # Use specific mode
            categories = [mode] if mode in self.SUGGESTIONS else list(self.SUGGESTIONS.keys())
        
        # Collect matching suggestions
        for category in categories:
            for suggestion in self.SUGGESTIONS.get(category, []):
                # Simple relevance scoring based on query match
                if query_lower in suggestion.text.lower():
                    # Boost score for exact matches
                    scored_suggestion = suggestion.copy()
                    scored_suggestion.score = min(1.0, suggestion.score + 0.1)
                    suggestions.append(scored_suggestion)
                elif any(word in suggestion.text.lower() for word in query_lower.split()):
                    # Partial word matches
                    suggestions.append(suggestion)
        
        # Sort by score and limit
        suggestions.sort(key=lambda x: x.score or 0, reverse=True)
        return suggestions[:limit]


# Initialize engine
suggestion_engine = SuggestionEngine()


@router.get("/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(
    partial_query: str = Query(..., description="Partial query string"),
    mode: str = Query('auto', description="Search mode"),
    limit: int = Query(10, ge=1, le=50, description="Maximum suggestions to return"),
    api_key: str = Depends(verify_api_key)
) -> SuggestionsResponse:
    """Get search suggestions based on partial query.
    
    This endpoint provides intelligent suggestions as the user types,
    helping them discover available actions and content.
    """
    try:
        # Get suggestions
        suggestions = await suggestion_engine.get_suggestions(
            partial_query,
            mode,
            limit
        )
        
        return SuggestionsResponse(suggestions=suggestions)
        
    except Exception as e:
        print(f"Suggestions error: {str(e)}")
        # Return empty suggestions on error
        return SuggestionsResponse(suggestions=[])