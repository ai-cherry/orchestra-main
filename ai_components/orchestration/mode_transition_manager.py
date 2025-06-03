"""Mode Transition Manager for seamless transitions between Roo modes."""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from ai_components.orchestration.roo_mcp_adapter import RooContext, RooMode
from shared.database import UnifiedDatabase
from shared.utils.error_handling import handle_errors
from shared.utils.performance import benchmark

logger = logging.getLogger(__name__)


class TransitionType(str, Enum):
    """Types of mode transitions."""

    AUTOMATIC = "automatic"  # System-initiated
    MANUAL = "manual"  # User-initiated
    SUGGESTED = "suggested"  # AI-suggested
    FALLBACK = "fallback"  # Error recovery


class TransitionState(str, Enum):
    """States of a transition."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TransitionContext:
    """Context preserved during mode transitions."""

    session_id: str
    from_mode: RooMode
    to_mode: RooMode
    task: str
    artifacts: Dict[str, Any] = field(default_factory=dict)
    messages: List[Dict[str, str]] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class TransitionRule(BaseModel):
    """Rule for automatic mode transitions."""

    name: str
    from_mode: RooMode
    to_mode: RooMode
    condition: str  # Python expression to evaluate
    priority: int = Field(default=0, ge=0, le=100)
    enabled: bool = True
    description: Optional[str] = None


class TransitionHistory(BaseModel):
    """Record of a mode transition."""

    id: str
    session_id: str
    from_mode: RooMode
    to_mode: RooMode
    transition_type: TransitionType
    state: TransitionState
    context: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None


class ModeTransitionManager:
    """Manages seamless transitions between Roo modes."""

    def __init__(self):
        """Initialize the transition manager."""
        self.active_transitions: Dict[str, TransitionContext] = {}
        self.transition_rules = self._initialize_transition_rules()
        self.transition_history: List[TransitionHistory] = []
        self._lock = asyncio.Lock()

    def _initialize_transition_rules(self) -> List[TransitionRule]:
        """Initialize automatic transition rules."""
        return [
            # Code to Debug transitions
            TransitionRule(
                name="code_error_to_debug",
                from_mode=RooMode.CODE,
                to_mode=RooMode.DEBUG,
                condition="'error' in context.get('last_result', {})",
                priority=90,
                description="Transition to debug mode on code errors",
            ),
            # Research to Implementation transitions
            TransitionRule(
                name="research_to_implementation",
                from_mode=RooMode.RESEARCH,
                to_mode=RooMode.IMPLEMENTATION,
                condition="context.get('research_complete', False)",
                priority=80,
                description="Move to implementation after research",
            ),
            # Architect to Code transitions
            TransitionRule(
                name="architect_to_code",
                from_mode=RooMode.ARCHITECT,
                to_mode=RooMode.CODE,
                condition="context.get('design_approved', False)",
                priority=85,
                description="Start coding after architecture approval",
            ),
            # Quality to Debug transitions
            TransitionRule(
                name="quality_issues_to_debug",
                from_mode=RooMode.QUALITY,
                to_mode=RooMode.DEBUG,
                condition="len(context.get('quality_issues', [])) > 0",
                priority=75,
                description="Debug quality issues",
            ),
            # Strategy to Research transitions
            TransitionRule(
                name="strategy_needs_research",
                from_mode=RooMode.STRATEGY,
                to_mode=RooMode.RESEARCH,
                condition="context.get('needs_research', False)",
                priority=70,
                description="Research for strategy decisions",
            ),
        ]

    @benchmark
    async def initiate_transition(
        self,
        session_id: str,
        from_mode: RooMode,
        to_mode: RooMode,
        context: Dict[str, Any],
        transition_type: TransitionType = TransitionType.MANUAL,
    ) -> str:
        """Initiate a mode transition.

        Args:
            session_id: Session identifier
            from_mode: Current mode
            to_mode: Target mode
            context: Current context
            transition_type: Type of transition

        Returns:
            Transition ID
        """
        async with self._lock:
            # Create transition context
            transition_id = f"trans_{datetime.utcnow().timestamp()}"
            transition_context = TransitionContext(
                session_id=session_id,
                from_mode=from_mode,
                to_mode=to_mode,
                task=context.get("task", ""),
                artifacts=context.get("artifacts", {}),
                messages=context.get("messages", []),
                files=context.get("files", []),
                metadata=context.get("metadata", {}),
            )

            # Store active transition
            self.active_transitions[transition_id] = transition_context

            # Create history record
            history = TransitionHistory(
                id=transition_id,
                session_id=session_id,
                from_mode=from_mode,
                to_mode=to_mode,
                transition_type=transition_type,
                state=TransitionState.PENDING,
                context=context,
                started_at=datetime.utcnow(),
            )
            self.transition_history.append(history)

            # Store in database
            await self._store_transition(history)

            logger.info(
                f"Initiated transition {transition_id}: "
                f"{from_mode.value} -> {to_mode.value}"
            )

            return transition_id

    @handle_errors
    async def execute_transition(self, transition_id: str) -> TransitionContext:
        """Execute a pending transition.

        Args:
            transition_id: Transition ID

        Returns:
            Updated transition context
        """
        if transition_id not in self.active_transitions:
            raise ValueError(f"Unknown transition: {transition_id}")

        transition_context = self.active_transitions[transition_id]
        history = next(
            (h for h in self.transition_history if h.id == transition_id), None
        )

        if not history:
            raise ValueError(f"No history for transition: {transition_id}")

        try:
            # Update state
            history.state = TransitionState.IN_PROGRESS
            await self._update_transition_state(transition_id, TransitionState.IN_PROGRESS)

            # Preserve context
            preserved_context = await self._preserve_context(transition_context)

            # Perform handoff
            handoff_result = await self._perform_handoff(
                transition_context, preserved_context
            )

            # Update artifacts
            transition_context.artifacts.update(handoff_result)

            # Complete transition
            history.state = TransitionState.COMPLETED
            history.completed_at = datetime.utcnow()
            history.duration_ms = int(
                (history.completed_at - history.started_at).total_seconds() * 1000
            )

            await self._update_transition_state(
                transition_id, TransitionState.COMPLETED, history.duration_ms
            )

            logger.info(
                f"Completed transition {transition_id} in {history.duration_ms}ms"
            )

            return transition_context

        except Exception as e:
            # Handle failure
            history.state = TransitionState.FAILED
            history.error = str(e)
            history.completed_at = datetime.utcnow()

            await self._update_transition_state(
                transition_id, TransitionState.FAILED, error=str(e)
            )

            logger.error(f"Transition {transition_id} failed: {e}")
            raise

        finally:
            # Clean up
            if transition_id in self.active_transitions:
                del self.active_transitions[transition_id]

    async def _preserve_context(
        self, transition: TransitionContext
    ) -> Dict[str, Any]:
        """Preserve context during transition.

        Args:
            transition: Transition context

        Returns:
            Preserved context data
        """
        preserved = {
            "session_id": transition.session_id,
            "from_mode": transition.from_mode.value,
            "to_mode": transition.to_mode.value,
            "task": transition.task,
            "timestamp": transition.timestamp.isoformat(),
            "artifacts": transition.artifacts.copy(),
            "messages": transition.messages.copy(),
            "files": transition.files.copy(),
            "metadata": transition.metadata.copy(),
        }

        # Mode-specific preservation
        if transition.from_mode == RooMode.CODE:
            preserved["code_context"] = {
                "last_code": transition.artifacts.get("last_code", ""),
                "language": transition.artifacts.get("language", "python"),
                "errors": transition.artifacts.get("errors", []),
            }
        elif transition.from_mode == RooMode.ARCHITECT:
            preserved["design_context"] = {
                "architecture": transition.artifacts.get("architecture", {}),
                "components": transition.artifacts.get("components", []),
                "decisions": transition.artifacts.get("decisions", []),
            }
        elif transition.from_mode == RooMode.RESEARCH:
            preserved["research_context"] = {
                "findings": transition.artifacts.get("findings", []),
                "sources": transition.artifacts.get("sources", []),
                "recommendations": transition.artifacts.get("recommendations", []),
            }

        return preserved

    async def _perform_handoff(
        self, transition: TransitionContext, preserved: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform context handoff between modes.

        Args:
            transition: Transition context
            preserved: Preserved context

        Returns:
            Handoff results
        """
        handoff = {
            "handoff_time": datetime.utcnow().isoformat(),
            "preserved_context": preserved,
        }

        # Generate handoff summary
        summary = await self._generate_handoff_summary(transition, preserved)
        handoff["summary"] = summary

        # Mode-specific handoff
        if transition.to_mode == RooMode.DEBUG:
            handoff["debug_context"] = {
                "error_context": preserved.get("code_context", {}).get("errors", []),
                "last_operation": transition.task,
                "relevant_files": transition.files,
            }
        elif transition.to_mode == RooMode.CODE:
            handoff["coding_context"] = {
                "requirements": preserved.get("design_context", {}).get(
                    "architecture", {}
                ),
                "previous_attempts": transition.artifacts.get("attempts", []),
            }
        elif transition.to_mode == RooMode.IMPLEMENTATION:
            handoff["implementation_context"] = {
                "research_findings": preserved.get("research_context", {}).get(
                    "findings", []
                ),
                "recommended_approach": preserved.get("research_context", {}).get(
                    "recommendations", []
                ),
            }

        return handoff

    async def _generate_handoff_summary(
        self, transition: TransitionContext, preserved: Dict[str, Any]
    ) -> str:
        """Generate a summary for the handoff.

        Args:
            transition: Transition context
            preserved: Preserved context

        Returns:
            Handoff summary
        """
        summary_parts = [
            f"Transitioning from {transition.from_mode.value} to {transition.to_mode.value}",
            f"Task: {transition.task}",
            f"Session: {transition.session_id}",
        ]

        # Add mode-specific summary
        if transition.from_mode == RooMode.CODE and "errors" in transition.artifacts:
            summary_parts.append(
                f"Errors encountered: {len(transition.artifacts['errors'])}"
            )
        elif transition.from_mode == RooMode.RESEARCH and "findings" in transition.artifacts:
            summary_parts.append(
                f"Research findings: {len(transition.artifacts['findings'])}"
            )

        return "\n".join(summary_parts)

    async def suggest_transition(
        self, session_id: str, current_mode: RooMode, context: Dict[str, Any]
    ) -> Optional[Tuple[RooMode, str]]:
        """Suggest a mode transition based on context.

        Args:
            session_id: Session identifier
            current_mode: Current mode
            context: Current context

        Returns:
            Tuple of (suggested_mode, reason) or None
        """
        applicable_rules = [
            rule
            for rule in self.transition_rules
            if rule.from_mode == current_mode and rule.enabled
        ]

        # Sort by priority
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)

        for rule in applicable_rules:
            try:
                # Evaluate condition safely
                if self._evaluate_condition(rule.condition, context):
                    return rule.to_mode, rule.description or rule.name
            except Exception as e:
                logger.warning(f"Error evaluating rule {rule.name}: {e}")

        return None

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Safely evaluate transition conditions.
        
        Args:
            condition: Condition string
            context: Context dictionary
            
        Returns:
            Boolean result of condition evaluation
        """
        # Safe condition evaluation without eval()
        if condition == "'error' in context.get('last_result', {})":
            return 'error' in context.get('last_result', {})
        elif condition == "context.get('research_complete', False)":
            return context.get('research_complete', False)
        elif condition == "context.get('design_approved', False)":
            return context.get('design_approved', False)
        elif condition == "len(context.get('quality_issues', [])) > 0":
            return len(context.get('quality_issues', [])) > 0
        elif condition == "context.get('needs_research', False)":
            return context.get('needs_research', False)
        else:
            logger.warning(f"Unknown condition: {condition}")
            return False

    async def get_transition_history(
        self,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[TransitionHistory]:
        """Get transition history.

        Args:
            session_id: Optional session filter
            limit: Maximum results

        Returns:
            List of transition history records
        """
        async with UnifiedDatabase() as db:
            query = """
                SELECT * FROM mode_transitions
                WHERE ($1::text IS NULL OR session_id = $1)
                ORDER BY created_at DESC
                LIMIT $2
            """
            rows = await db.fetch_all(query, session_id, limit)

            return [
                TransitionHistory(
                    id=row["id"],
                    session_id=row["session_id"],
                    from_mode=RooMode(row["from_mode"]),
                    to_mode=RooMode(row["to_mode"]),
                    transition_type=TransitionType(row["transition_type"]),
                    state=TransitionState(row["state"]),
                    context=json.loads(row["context"]),
                    started_at=row["started_at"],
                    completed_at=row["completed_at"],
                    duration_ms=row["duration_ms"],
                    error=row["error"],
                )
                for row in rows
            ]

    async def analyze_transition_patterns(self) -> Dict[str, Any]:
        """Analyze transition patterns for optimization.

        Returns:
            Analysis results
        """
        async with UnifiedDatabase() as db:
            # Get transition statistics
            stats_query = """
                SELECT 
                    from_mode,
                    to_mode,
                    COUNT(*) as count,
                    AVG(duration_ms) as avg_duration,
                    SUM(CASE WHEN state = 'failed' THEN 1 ELSE 0 END) as failures
                FROM mode_transitions
                WHERE created_at > NOW() - INTERVAL '7 days'
                GROUP BY from_mode, to_mode
                ORDER BY count DESC
            """
            stats = await db.fetch_all(stats_query)

            # Get success rates
            success_query = """
                SELECT 
                    from_mode,
                    to_mode,
                    COUNT(*) FILTER (WHERE state = 'completed') * 100.0 / 
                    NULLIF(COUNT(*), 0) as success_rate
                FROM mode_transitions
                WHERE created_at > NOW() - INTERVAL '7 days'
                GROUP BY from_mode, to_mode
            """
            success_rates = await db.fetch_all(success_query)

            return {
                "transition_stats": [dict(row) for row in stats],
                "success_rates": [dict(row) for row in success_rates],
                "total_transitions": sum(row["count"] for row in stats),
                "most_common": stats[0] if stats else None,
            }

    async def _store_transition(self, history: TransitionHistory) -> None:
        """Store transition in database.

        Args:
            history: Transition history record
        """
        async with UnifiedDatabase() as db:
            await db.execute(
                """
                INSERT INTO mode_transitions 
                (id, session_id, from_mode, to_mode, transition_type, 
                 state, context, started_at, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                history.id,
                history.session_id,
                history.from_mode.value,
                history.to_mode.value,
                history.transition_type.value,
                history.state.value,
                json.dumps(history.context),
                history.started_at,
                datetime.utcnow(),
            )

    async def _update_transition_state(
        self,
        transition_id: str,
        state: TransitionState,
        duration_ms: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update transition state in database.

        Args:
            transition_id: Transition ID
            state: New state
            duration_ms: Duration in milliseconds
            error: Error message if failed
        """
        async with UnifiedDatabase() as db:
            await db.execute(
                """
                UPDATE mode_transitions 
                SET state = $2, 
                    completed_at = CASE WHEN $2 IN ('completed', 'failed') 
                                       THEN NOW() ELSE NULL END,
                    duration_ms = $3,
                    error = $4,
                    updated_at = NOW()
                WHERE id = $1
                """,
                transition_id,
                state.value,
                duration_ms,
                error,
            )