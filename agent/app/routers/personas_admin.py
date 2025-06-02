"""Personas Admin API endpoints for managing persona configurations."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from core.personas import (
    PersonaConfigError,
    PersonaConfigManager,
    PersonaConfiguration,
    PersonaNotFoundError,
    PersonaStatus,
)

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/personas", tags=["personas-admin"])

# Initialize PersonaConfigManager - this should be configured with the actual path
# In production, this would be injected via dependency injection
PERSONAS_CONFIG_DIR = Path("config/personas")
persona_manager: Optional[PersonaConfigManager] = None


def get_persona_manager() -> PersonaConfigManager:
    """
    Get or initialize the PersonaConfigManager instance.

    Returns:
        PersonaConfigManager: The initialized manager instance

    Raises:
        HTTPException: If manager initialization fails
    """
    global persona_manager

    if persona_manager is None:
        try:
            persona_manager = PersonaConfigManager(PERSONAS_CONFIG_DIR)
            persona_manager.load_all_personas()
            logger.info(f"Initialized PersonaConfigManager with {len(persona_manager.personas)} personas")
        except PersonaConfigError as e:
            logger.error(f"Failed to initialize PersonaConfigManager: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize persona manager: {str(e)}",
            )

    return persona_manager


def verify_api_key(x_api_key: str = Header(None)) -> str:
    """
    Verify API key authentication.

    Args:
        x_api_key: API key from request header

    Returns:
        str: The validated API key

    Raises:
        HTTPException: If API key is invalid
    """
    expected_key = "4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd"
    if x_api_key != expected_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    return x_api_key


class PersonaListResponse(BaseModel):
    """Response model for persona list endpoint."""

    personas: List[PersonaConfiguration]
    total: int = Field(..., description="Total number of personas")
    filtered: int = Field(..., description="Number of personas after filtering")


class PersonaUpdateRequest(BaseModel):
    """Request model for updating persona configuration."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    status: Optional[PersonaStatus] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=100, le=32000)
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    allowed_users: Optional[List[str]] = None
    allowed_roles: Optional[List[str]] = None

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {"example": {"status": "active", "temperature": 0.7, "tags": ["updated", "technical"]}}


class PersonaExportRequest(BaseModel):
    """Request model for exporting persona configuration."""

    output_path: str = Field(..., description="Path where to export the persona YAML")


class ValidationReport(BaseModel):
    """Response model for validation endpoint."""

    valid: bool = Field(..., description="Whether all personas are valid")
    issues: Dict[str, List[str]] = Field(default_factory=dict, description="Map of persona slugs to validation issues")
    total_personas: int = Field(..., description="Total number of personas validated")
    personas_with_issues: int = Field(..., description="Number of personas with issues")


@router.get("/", response_model=PersonaListResponse)
async def list_personas(
    status: Optional[PersonaStatus] = None, tags: Optional[str] = None, api_key: str = Depends(verify_api_key)
) -> PersonaListResponse:
    """
    List all available personas with optional filtering.

    Args:
        status: Filter by persona status
        tags: Comma-separated list of tags to filter by
        api_key: API key for authentication

    Returns:
        PersonaListResponse: List of personas with metadata
    """
    try:
        manager = get_persona_manager()

        # Parse tags if provided
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Get filtered personas
        filtered_personas = manager.list_personas(status=status, tags=tag_list)

        # Get total count
        total_personas = len(manager.personas)

        return PersonaListResponse(personas=filtered_personas, total=total_personas, filtered=len(filtered_personas))

    except Exception as e:
        logger.error(f"Error listing personas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list personas: {str(e)}"
        )


@router.get("/{slug}", response_model=PersonaConfiguration)
async def get_persona(slug: str, api_key: str = Depends(verify_api_key)) -> PersonaConfiguration:
    """
    Get a specific persona by slug.

    Args:
        slug: The slug identifier of the persona
        api_key: API key for authentication

    Returns:
        PersonaConfiguration: The requested persona configuration

    Raises:
        HTTPException: If persona not found
    """
    try:
        manager = get_persona_manager()
        persona = manager.get_persona(slug)
        return persona

    except PersonaNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Persona not found: {slug}")
    except Exception as e:
        logger.error(f"Error getting persona {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get persona: {str(e)}"
        )


@router.put("/{slug}", response_model=PersonaConfiguration)
async def update_persona(
    slug: str, update_request: PersonaUpdateRequest, api_key: str = Depends(verify_api_key)
) -> PersonaConfiguration:
    """
    Update a persona configuration.

    Note: This endpoint updates the in-memory configuration only.
    To persist changes, use the export endpoint.

    Args:
        slug: The slug identifier of the persona
        update_request: Fields to update
        api_key: API key for authentication

    Returns:
        PersonaConfiguration: The updated persona configuration

    Raises:
        HTTPException: If persona not found or update fails
    """
    try:
        manager = get_persona_manager()
        persona = manager.get_persona(slug)

        # Update fields that were provided
        update_data = update_request.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(persona, field):
                setattr(persona, field, value)

        # Update the timestamp
        from datetime import datetime

        persona.updated_at = datetime.utcnow()

        # Store updated persona back in manager
        manager.personas[slug] = persona

        logger.info(f"Updated persona: {slug}")
        return persona

    except PersonaNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Persona not found: {slug}")
    except Exception as e:
        logger.error(f"Error updating persona {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update persona: {str(e)}"
        )


@router.post("/{slug}/reload", response_model=PersonaConfiguration)
async def reload_persona(slug: str, api_key: str = Depends(verify_api_key)) -> PersonaConfiguration:
    """
    Reload a persona from its configuration file.

    This will discard any in-memory changes and reload from disk.

    Args:
        slug: The slug identifier of the persona
        api_key: API key for authentication

    Returns:
        PersonaConfiguration: The reloaded persona configuration

    Raises:
        HTTPException: If persona not found or reload fails
    """
    try:
        manager = get_persona_manager()
        persona = manager.reload_persona(slug)
        return persona

    except PersonaNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Persona not found: {slug}")
    except Exception as e:
        logger.error(f"Error reloading persona {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to reload persona: {str(e)}"
        )


@router.get("/validate/all", response_model=ValidationReport)
async def validate_all_personas(api_key: str = Depends(verify_api_key)) -> ValidationReport:
    """
    Validate all loaded personas and return validation report.

    Args:
        api_key: API key for authentication

    Returns:
        ValidationReport: Validation results for all personas
    """
    try:
        manager = get_persona_manager()
        issues = manager.validate_all()

        return ValidationReport(
            valid=len(issues) == 0,
            issues=issues,
            total_personas=len(manager.personas),
            personas_with_issues=len(issues),
        )

    except Exception as e:
        logger.error(f"Error validating personas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to validate personas: {str(e)}"
        )


@router.post("/{slug}/export")
async def export_persona(
    slug: str, export_request: PersonaExportRequest, api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Export a persona configuration to a YAML file.

    Args:
        slug: The slug identifier of the persona
        export_request: Export configuration including output path
        api_key: API key for authentication

    Returns:
        Dict: Export status and file path

    Raises:
        HTTPException: If persona not found or export fails
    """
    try:
        manager = get_persona_manager()
        output_path = Path(export_request.output_path)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Export the persona
        manager.export_persona(slug, output_path)

        return {
            "status": "success",
            "message": f"Persona '{slug}' exported successfully",
            "output_path": str(output_path),
            "slug": slug,
        }

    except PersonaNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Persona not found: {slug}")
    except IOError as e:
        logger.error(f"Error exporting persona {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to export persona: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error exporting persona {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to export persona: {str(e)}"
        )


@router.post("/check-updates")
async def check_for_updates(api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    Check for updated persona files and reload them.

    This endpoint scans for modified persona files and reloads
    any that have changed since they were last loaded.

    Args:
        api_key: API key for authentication

    Returns:
        Dict: Update status and list of updated personas
    """
    try:
        manager = get_persona_manager()
        updated_personas = manager.check_for_updates()

        return {
            "status": "success",
            "updated_count": len(updated_personas),
            "updated_personas": list(updated_personas),
            "message": f"Checked for updates, {len(updated_personas)} personas reloaded",
        }

    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to check for updates: {str(e)}"
        )


@router.get("/health/status")
async def personas_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for personas admin service.

    Returns:
        Dict: Health status information
    """
    try:
        manager = get_persona_manager()

        return {
            "status": "healthy",
            "service": "personas-admin",
            "personas_loaded": len(manager.personas),
            "config_dir": str(PERSONAS_CONFIG_DIR),
            "manager_initialized": persona_manager is not None,
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "personas-admin",
            "error": str(e),
            "manager_initialized": persona_manager is not None,
        }
