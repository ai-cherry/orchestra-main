"""Intent detection API endpoints for OmniSearch functionality."""

from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import re

from agent.app.routers.admin import verify_api_key

router = APIRouter(prefix="/api/intent", tags=["intent"])

class IntentRequest(BaseModel):
    """Request model for intent detection."""

    query: str
    context: Optional[Dict] = None

class IntentResponse(BaseModel):
    """Response model for intent detection."""

    type: str
    confidence: float
    entities: Optional[Dict] = None

class IntentDetector:
    """Simple rule-based intent detection for MVP.

    In production, this would use NLP models for better accuracy.
    """

    # Intent patterns
    PATTERNS = {
        "agent_creation": [r"create.*agent", r"build.*agent", r"new.*agent", r"make.*agent", r"design.*agent"],
        "workflow": [r"create.*workflow", r"build.*automation", r"new.*flow", r"design.*process"],
        "search": [r"^search", r"^find", r"^look for", r"^show me", r"^list"],
        "generate": [r"generate", r"create.*content", r"write", r"produce", r"make.*for me"],
        "command": [r"^/", r"^run", r"^execute", r"^perform", r"^do"],
        "media_generation": [r"create.*image", r"generate.*video", r"make.*picture", r"design.*graphic"],
    }

    def detect(self, query: str) -> IntentResponse:
        """Detect intent from query string."""
        query_lower = query.lower().strip()

        # Check each pattern category
        for intent_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    # Calculate confidence based on pattern match strength
                    confidence = 0.9 if re.match(pattern, query_lower) else 0.7

                    # Extract entities (simplified)
                    entities = self._extract_entities(query_lower, intent_type)

                    return IntentResponse(type=intent_type, confidence=confidence, entities=entities)

        # Default to search if no pattern matches
        return IntentResponse(type="search", confidence=0.5, entities=None)

    def _extract_entities(self, query: str, intent_type: str) -> Optional[Dict]:
        """Extract relevant entities from query."""
        entities = {}

        if intent_type == "agent_creation":
            # Extract agent type if mentioned
            agent_types = ["assistant", "analyzer", "monitor", "generator"]
            for agent_type in agent_types:
                if agent_type in query:
                    entities["agent_type"] = agent_type
                    break

        elif intent_type == "media_generation":
            # Extract media type
            if "image" in query or "picture" in query:
                entities["media_type"] = "image"
            elif "video" in query:
                entities["media_type"] = "video"

        return entities if entities else None

# Initialize detector
detector = IntentDetector()

@router.post("/detect", response_model=IntentResponse)
async def detect_intent(request: IntentRequest, api_key: str = Depends(verify_api_key)) -> IntentResponse:
    """Detect intent from user query.

    This endpoint analyzes the user's query to determine their intent,
    which helps the UI provide appropriate suggestions and actions.
    """
    try:
        # Perform intent detection
        result = detector.detect(request.query)

        # Log for monitoring
        print(f"Intent detected: {result.type} (confidence: {result.confidence}) for query: '{request.query}'")

        return result

    except Exception as e:
        print(f"Intent detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Intent detection failed: {str(e)}")
