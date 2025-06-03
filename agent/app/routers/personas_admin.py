"""Personas Admin API endpoints for managing persona configurations."""
router = APIRouter(prefix="/api/personas", tags=["personas-admin"])

# Initialize PersonaConfigManager - this should be configured with the actual path
# In production, this would be injected via dependency injection
PERSONAS_CONFIG_DIR = Path("config/personas")
persona_manager: Optional[PersonaConfigManager] = None

def get_persona_manager() -> PersonaConfigManager:
    """
    """
            logger.info(f"Initialized PersonaConfigManager with {len(persona_manager.personas)} personas")
        except Exception:

            pass
            logger.error(f"Failed to initialize PersonaConfigManager: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize persona manager: {str(e)}",
            )

    return persona_manager

def verify_api_key(x_api_key: str = Header(None)) -> str:
    """
    """
    expected_key = "4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd"
    if x_api_key != expected_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    return x_api_key

class PersonaListResponse(BaseModel):
    """Response model for persona list endpoint."""
    total: int = Field(..., description="Total number of personas")
    filtered: int = Field(..., description="Number of personas after filtering")

class PersonaUpdateRequest(BaseModel):
    """Request model for updating persona configuration."""
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
    """
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Get filtered personas
        filtered_personas = manager.list_personas(status=status, tags=tag_list)

        # Get total count
        total_personas = len(manager.personas)

        return PersonaListResponse(personas=filtered_personas, total=total_personas, filtered=len(filtered_personas))

    except Exception:


        pass
        logger.error(f"Error listing personas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list personas: {str(e)}"
        )

@router.get("/{slug}", response_model=PersonaConfiguration)
async def get_persona(slug: str, api_key: str = Depends(verify_api_key)) -> PersonaConfiguration:
    """
    """
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Persona not found: {slug}")
    except Exception:

        pass
        logger.error(f"Error getting persona {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get persona: {str(e)}"
        )

@router.put("/{slug}", response_model=PersonaConfiguration)
async def update_persona(
    slug: str, update_request: PersonaUpdateRequest, api_key: str = Depends(verify_api_key)
) -> PersonaConfiguration:
    """
    """
        logger.info(f"Updated persona: {slug}")
        return persona

    except Exception:


        pass
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Persona not found: {slug}")
    except Exception:

        pass
        logger.error(f"Error updating persona {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update persona: {str(e)}"
        )

@router.post("/{slug}/reload", response_model=PersonaConfiguration)
async def reload_persona(slug: str, api_key: str = Depends(verify_api_key)) -> PersonaConfiguration:
    """
    """
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Persona not found: {slug}")
    except Exception:

        pass
        logger.error(f"Error reloading persona {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to reload persona: {str(e)}"
        )

@router.get("/validate/all", response_model=ValidationReport)
async def validate_all_personas(api_key: str = Depends(verify_api_key)) -> ValidationReport:
    """
    """
        logger.error(f"Error validating personas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to validate personas: {str(e)}"
        )

@router.post("/{slug}/export")
async def export_persona(
    slug: str, export_request: PersonaExportRequest, api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    """
            "status": "success",
            "message": f"Persona '{slug}' exported successfully",
            "output_path": str(output_path),
            "slug": slug,
        }

    except Exception:


        pass
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Persona not found: {slug}")
    except Exception:

        pass
        logger.error(f"Error exporting persona {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to export persona: {str(e)}"
        )
    except Exception:

        pass
        logger.error(f"Unexpected error exporting persona {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to export persona: {str(e)}"
        )

@router.post("/check-updates")
async def check_for_updates(api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    """
            "status": "success",
            "updated_count": len(updated_personas),
            "updated_personas": list(updated_personas),
            "message": f"Checked for updates, {len(updated_personas)} personas reloaded",
        }

    except Exception:


        pass
        logger.error(f"Error checking for updates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to check for updates: {str(e)}"
        )

@router.get("/health/status")
async def personas_health_check() -> Dict[str, Any]:
    """
    """
            "status": "healthy",
            "service": "personas-admin",
            "personas_loaded": len(manager.personas),
            "config_dir": str(PERSONAS_CONFIG_DIR),
            "manager_initialized": persona_manager is not None,
        }

    except Exception:


        pass
        return {
            "status": "unhealthy",
            "service": "personas-admin",
            "error": str(e),
            "manager_initialized": persona_manager is not None,
        }
