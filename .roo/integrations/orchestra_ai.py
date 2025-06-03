#!/usr/bin/env python3
"""Orchestra AI integration for Roo Coder"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Global integration instance
_orchestra_integration = None


def get_orchestra_integration():
    """Get or create the Orchestra integration instance."""
    global _orchestra_integration
    if _orchestra_integration is None:
        try:
            from mcp_server.roo.orchestra_integration import OrchestraRooIntegration
            _orchestra_integration = OrchestraRooIntegration()
            logger.info("🎭 Orchestra AI integration created")
        except Exception as e:
            logger.error(f"Failed to create Orchestra integration: {e}")
            _orchestra_integration = None
    
    return _orchestra_integration


async def _initialize_integration():
    """Initialize the Orchestra AI integration"""
    integration = get_orchestra_integration()
    if integration:
        try:
            await integration.initialize()
            logger.info("✅ Orchestra AI integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Orchestra integration: {e}")


class OrchestraEnhancedMode:
    """Base class for Orchestra-enhanced Roo modes"""
    
    def __init__(self, mode_name: str):
        self.mode_name = mode_name
        self.integration = get_orchestra_integration()
    
    async def process_request(self, request: str) -> str:
        """Process request with Orchestra AI enhancement."""
        if not self.integration:
            return request
        
        try:
            enhanced = await self.integration.enhance_request(self.mode_name, request)
            return enhanced.get("enhanced_request", request)
        except Exception as e:
            logger.error(f"Orchestra processing error: {e}")
            return request


class CodeModeEnhancement(OrchestraEnhancedMode):
    """Orchestra enhancement for code mode."""
    
    def __init__(self):
        super().__init__("code")
    
    async def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code using Orchestra AI agents"""
        if not self.integration:
            return {"analysis": "Integration not available"}
        
        return await self.integration.analyze_code({
            "code": code,
            "language": language,
            "mode": "code"
        })
    
    async def suggest_improvements(self, code: str) -> Dict[str, Any]:
        """Get code improvement suggestions"""
        if not self.integration:
            return {"suggestions": []}
        
        return await self.integration.get_suggestions({
            "code": code,
            "type": "improvements"
        })


class ArchitectModeEnhancement(OrchestraEnhancedMode):
    """Orchestra enhancement for architect mode."""
    
    def __init__(self):
        super().__init__("architect")
    
    async def design_system(self, requirements: str) -> Dict[str, Any]:
        """Design system architecture using Orchestra AI"""
        if not self.integration:
            return {"design": "Integration not available"}
        
        return await self.integration.design_architecture({
            "requirements": requirements,
            "mode": "architect"
        })


class DebugModeEnhancement(OrchestraEnhancedMode):
    """Orchestra enhancement for debug mode."""
    
    def __init__(self):
        super().__init__("debug")
    
    async def analyze_error(self, error: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze error using Orchestra AI debugging agents"""
        if not self.integration:
            return {"analysis": "Integration not available"}
        
        return await self.integration.debug_error({
            "error": error,
            "context": context,
            "mode": "debug"
        })


def initialize_orchestra_integration():
    """Initialize Orchestra AI integration with Roo"""
    try:
        # Import Roo's hook system if available
        try:
            from roo.hooks import register_hook
            
            # Register mode enhancement hooks
            def on_mode_enter(mode_name: str):
                """Hook called when entering a mode"""
                integration = get_orchestra_integration()
                if integration:
                    logger.info(f"Orchestra AI enhancing {mode_name} mode")
            
            register_hook("mode_enter", on_mode_enter)
            logger.info("✅ Orchestra hooks registered")
        except ImportError:
            logger.warning("Roo hooks not available, running in standalone mode")
        
        # Initialize the integration
        import asyncio
        asyncio.create_task(_initialize_integration())
        
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Orchestra integration: {e}")
        return False


# Mode enhancement instances
code_enhancement = CodeModeEnhancement()
architect_enhancement = ArchitectModeEnhancement()
debug_enhancement = DebugModeEnhancement()


# Export public API
__all__ = [
    "initialize_orchestra_integration",
    "get_orchestra_integration",
    "code_enhancement",
    "architect_enhancement",
    "debug_enhancement"
]


def get_integration_status() -> Dict[str, Any]:
    """Get current integration status"""
    integration = get_orchestra_integration()
    if integration:
        return {
            "available": True,
            "modes_enhanced": ["code", "architect", "debug"],
            "status": "active"
        }
    else:
        return {"available": False}
