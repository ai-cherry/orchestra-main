"""
"""
@router.get("/", response_model=list[str])
async def get_personas() -> list[str]:
    """
    """
@router.get("/reload", response_model=dict)
async def reload_personas() -> dict:
    """
    """
            "status": "success",
            "message": f"Successfully reloaded {len(personas)} personas",
            "personas": list(personas.keys()),
        }
    except Exception:

        pass
        raise HTTPException(status_code=500, detail=f"Failed to reload personas: {str(e)}")

@router.get("/{name}", response_model=PersonaConfig)
async def get_persona(name: str) -> PersonaConfig:
    """
    """
        raise HTTPException(status_code=404, detail=f"Persona '{name}' not found")
    return personas[name]

@router.post("/", status_code=201)
async def create_persona(persona_config: PersonaConfig, settings: Settings = Depends(get_settings)):
    """
    """
        raise HTTPException(status_code=400, detail="Persona name is required")

    # Convert name to lowercase for the filename
    name_lower = persona_config.name.lower()

    # Check if the persona already exists
    personas = load_persona_configs()
    if name_lower in personas:
        raise HTTPException(status_code=409, detail=f"Persona '{persona_config.name}' already exists")

    # Get the persona file path
    persona_dir = os.path.dirname(os.path.join(os.path.dirname(__file__), "../../config/personas.yaml"))

    # Ensure the persona directory exists
    os.makedirs(persona_dir, exist_ok=True)

    yaml_path = os.path.join(persona_dir, "personas.yaml")

    try:


        pass
        # Load existing personas.yaml
        try:

            pass
            with open(yaml_path, "r") as file:
                existing_personas = yaml.safe_load(file) or {}
        except Exception:

            pass
            existing_personas = {}

        # Add new persona
        existing_personas[name_lower] = persona_config.model_dump(exclude_none=True)

        # Write updated personas.yaml
        with open(yaml_path, "w") as file:
            yaml_content = yaml.dump(existing_personas, sort_keys=False)
            file.write(yaml_content)

        # Force reload personas
        force_reload_personas()

        return {
            "status": "success",
            "message": f"Persona '{persona_config.name}' has been created successfully",
            "persona": persona_config,
        }
    except Exception:

        pass
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create persona '{persona_config.name}': {str(e)}",
        )

@router.post("/{name}/update", status_code=200)
async def update_persona(name: str, persona_config: PersonaConfig, settings: Settings = Depends(get_settings)):
    """
    """
        raise HTTPException(status_code=404, detail=f"Persona '{name}' not found")

    # Get the persona file path
    persona_dir = os.path.dirname(os.path.join(os.path.dirname(__file__), "../../config/personas.yaml"))
    yaml_path = os.path.join(persona_dir, "personas.yaml")

    # Ensure the persona name in the config matches the requested name
    persona_config.name = name

    try:


        pass
        # Load existing personas.yaml
        with open(yaml_path, "r") as file:
            existing_personas = yaml.safe_load(file) or {}

        # Update persona
        existing_personas[name_lower] = persona_config.model_dump(exclude_none=True)

        # Write updated personas.yaml
        with open(yaml_path, "w") as file:
            yaml_content = yaml.dump(existing_personas, sort_keys=False)
            file.write(yaml_content)

        # Force reload personas
        force_reload_personas()

        return {
            "status": "success",
            "message": f"Persona '{name}' has been updated successfully",
        }
    except Exception:

        pass
        raise HTTPException(status_code=500, detail=f"Failed to update persona '{name}': {str(e)}")

@router.delete("/{name}", status_code=status.HTTP_200_OK)
async def delete_persona(name: str, settings: Settings = Depends(get_settings)):
    """
    """
        raise HTTPException(status_code=404, detail=f"Persona '{name}' not found")

    # Get the persona file path
    persona_dir = os.path.dirname(os.path.join(os.path.dirname(__file__), "../../config/personas.yaml"))
    yaml_path = os.path.join(persona_dir, "personas.yaml")

    try:


        pass
        # Load existing personas.yaml
        with open(yaml_path, "r") as file:
            existing_personas = yaml.safe_load(file) or {}

        # Remove persona
        if name_lower in existing_personas:
            del existing_personas[name_lower]
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Persona '{name}' not found in configuration file",
            )

        # Write updated personas.yaml
        with open(yaml_path, "w") as file:
            yaml_content = yaml.dump(existing_personas, sort_keys=False)
            file.write(yaml_content)

        # Force reload personas
        force_reload_personas()

        return {
            "status": "success",
            "message": f"Persona '{name}' has been deleted successfully",
        }
    except Exception:

        pass
        # Re-raise HTTP except Exception:
     pass
        raise HTTPException(status_code=500, detail=f"Failed to delete persona '{name}': {str(e)}")
