"""
"""
    """Create a temporary directory for test configurations."""
    """Provide sample persona data for testing."""
        "name": "Test Persona",
        "slug": "test-persona",
        "description": "A test persona for unit testing",
        "status": "active",
        "created_by": "test_user",
        "traits": [
            {
                "name": "analytical_thinking",
                "category": "cognitive",
                "value": 85,
                "weight": 2.0,
                "description": "Test trait",
            }
        ],
        "response_style": {
            "type": "formal",
            "tone": "professional",
            "formality_level": 8,
            "verbosity": 6,
            "use_examples": True,
        },
        "interaction_mode": "analytical",
        "temperature": 0.7,
        "max_tokens": 2000,
    }

@pytest.fixture
def manager_with_personas(temp_config_dir: Path, sample_persona_data: dict) -> PersonaConfigManager:
    """Create a manager with pre-loaded test personas."""
    test_file = temp_config_dir / "test_personas.yaml"
    with open(test_file, "w") as f:
        yaml.dump(sample_persona_data, f)

    manager = PersonaConfigManager(temp_config_dir)
    manager.load_all_personas()
    return manager

class TestPersonaConfigManager:
    """Test cases for PersonaConfigManager."""
        """Test initialization with non-existent directory."""
        with pytest.raises(PersonaConfigError, match="Config directory does not exist"):
            PersonaConfigManager("/non/existent/path")

    def test_init_with_valid_directory(self, temp_config_dir: Path) -> None:
        """Test successful initialization."""
        """Test loading a single persona from file."""
        test_file = temp_config_dir / "test_persona.yaml"
        with open(test_file, "w") as f:
            yaml.dump(sample_persona_data, f)

        manager = PersonaConfigManager(temp_config_dir)
        persona = manager.load_persona_from_file(test_file)

        assert isinstance(persona, PersonaConfiguration)
        assert persona.name == "Test Persona"
        assert persona.slug == "test-persona"
        assert persona.status == PersonaStatus.ACTIVE
        assert len(persona.traits) == 1
        assert persona.traits[0].name == "analytical_thinking"

    def test_load_persona_from_nonexistent_file(self, temp_config_dir: Path) -> None:
        """Test loading from non-existent file."""
        with pytest.raises(PersonaConfigError, match="Persona file not found"):
            manager.load_persona_from_file(temp_config_dir / "nonexistent.yaml")

    def test_load_persona_with_invalid_yaml(self, temp_config_dir: Path) -> None:
        """Test loading file with invalid YAML syntax."""
        test_file = temp_config_dir / "invalid.yaml"
        with open(test_file, "w") as f:
            f.write("invalid: yaml: content: [")

        manager = PersonaConfigManager(temp_config_dir)

        with pytest.raises(PersonaConfigError, match="Invalid YAML"):
            manager.load_persona_from_file(test_file)

    def test_load_persona_with_empty_file(self, temp_config_dir: Path) -> None:
        """Test loading empty configuration file."""
        test_file = temp_config_dir / "empty.yaml"
        test_file.touch()

        manager = PersonaConfigManager(temp_config_dir)

        with pytest.raises(PersonaConfigError, match="Empty configuration file"):
            manager.load_persona_from_file(test_file)

    def test_load_persona_with_invalid_data(self, temp_config_dir: Path) -> None:
        """Test loading file with invalid persona data."""
        test_file = temp_config_dir / "invalid_persona.yaml"
        invalid_data = {"name": "Test", "slug": "test"}  # Missing required fields
        with open(test_file, "w") as f:
            yaml.dump(invalid_data, f)

        manager = PersonaConfigManager(temp_config_dir)

        with pytest.raises(PersonaConfigError, match="Invalid persona configuration"):
            manager.load_persona_from_file(test_file)

    def test_load_all_personas(self, temp_config_dir: Path, sample_persona_data: dict) -> None:
        """Test loading all personas from directory."""
            test_data["name"] = f"Test Persona {i}"
            test_data["slug"] = f"test-persona-{i}"

            test_file = temp_config_dir / f"persona_{i}.yaml"
            with open(test_file, "w") as f:
                yaml.dump(test_data, f)

        manager = PersonaConfigManager(temp_config_dir)
        personas = manager.load_all_personas()

        assert len(personas) == 3
        assert all(slug.startswith("test-persona-") for slug in personas.keys())

    def test_load_all_personas_empty_directory(self, temp_config_dir: Path) -> None:
        """Test loading from empty directory."""
        """Test loading with some invalid files."""
        valid_file = temp_config_dir / "valid.yaml"
        with open(valid_file, "w") as f:
            yaml.dump(sample_persona_data, f)

        # Create one invalid file
        invalid_file = temp_config_dir / "invalid.yaml"
        with open(invalid_file, "w") as f:
            f.write("invalid: yaml: [")

        manager = PersonaConfigManager(temp_config_dir)
        personas = manager.load_all_personas()

        assert len(personas) == 1
        assert "test-persona" in personas

    def test_get_persona(self, manager_with_personas: PersonaConfigManager) -> None:
        """Test retrieving a specific persona."""
        persona = manager_with_personas.get_persona("test-persona")
        assert persona.name == "Test Persona"
        assert persona.slug == "test-persona"

    def test_get_persona_not_found(self, manager_with_personas: PersonaConfigManager) -> None:
        """Test retrieving non-existent persona."""
        with pytest.raises(PersonaNotFoundError, match="Persona not found: nonexistent"):
            manager_with_personas.get_persona("nonexistent")

    def test_list_personas(self, manager_with_personas: PersonaConfigManager) -> None:
        """Test listing all personas."""
        assert personas[0].slug == "test-persona"

    def test_list_personas_with_status_filter(self, temp_config_dir: Path, sample_persona_data: dict) -> None:
        """Test listing personas filtered by status."""
        for status in ["active", "inactive", "draft"]:
            data = sample_persona_data.copy()
            data["slug"] = f"persona-{status}"
            data["status"] = status

            test_file = temp_config_dir / f"{status}.yaml"
            with open(test_file, "w") as f:
                yaml.dump(data, f)

        manager = PersonaConfigManager(temp_config_dir)
        manager.load_all_personas()

        active_personas = manager.list_personas(status=PersonaStatus.ACTIVE)
        assert len(active_personas) == 1
        assert active_personas[0].status == PersonaStatus.ACTIVE

    def test_list_personas_with_tag_filter(self, temp_config_dir: Path, sample_persona_data: dict) -> None:
        """Test listing personas filtered by tags."""
        for i, tags in enumerate([["tag1", "tag2"], ["tag2", "tag3"], ["tag3"]]):
            data = sample_persona_data.copy()
            data["slug"] = f"persona-{i}"
            data["tags"] = tags

            test_file = temp_config_dir / f"persona_{i}.yaml"
            with open(test_file, "w") as f:
                yaml.dump(data, f)

        manager = PersonaConfigManager(temp_config_dir)
        manager.load_all_personas()

        # Filter by single tag
        tag2_personas = manager.list_personas(tags=["tag2"])
        assert len(tag2_personas) == 2

        # Filter by multiple tags
        multi_tag_personas = manager.list_personas(tags=["tag2", "tag3"])
        assert len(multi_tag_personas) == 1

    def test_reload_persona(self, temp_config_dir: Path, sample_persona_data: dict) -> None:
        """Test reloading a specific persona."""
        test_file = temp_config_dir / "test.yaml"
        with open(test_file, "w") as f:
            yaml.dump(sample_persona_data, f)

        manager = PersonaConfigManager(temp_config_dir)
        manager.load_all_personas()

        # Modify the file
        sample_persona_data["description"] = "Updated description"
        with open(test_file, "w") as f:
            yaml.dump(sample_persona_data, f)

        # Reload
        reloaded = manager.reload_persona("test-persona", test_file)
        assert reloaded.description == "Updated description"

    def test_check_for_updates(self, temp_config_dir: Path, sample_persona_data: dict) -> None:
        """Test checking for file updates."""
        test_file = temp_config_dir / "test.yaml"
        with open(test_file, "w") as f:
            yaml.dump(sample_persona_data, f)

        manager = PersonaConfigManager(temp_config_dir)
        manager.load_all_personas()

        # No updates initially
        updated = manager.check_for_updates()
        assert len(updated) == 0

        # Modify file
        import time

        # TODO: Replace with asyncio.sleep() for async code
        time.sleep(0.1)  # Ensure mtime changes
        sample_persona_data["description"] = "Updated"
        with open(test_file, "w") as f:
            yaml.dump(sample_persona_data, f)

        # Check for updates
        updated = manager.check_for_updates()
        assert "test-persona" in updated

    def test_validate_all(self, temp_config_dir: Path, sample_persona_data: dict) -> None:
        """Test validation of all personas."""
        invalid_data["slug"] = "invalid-persona"
        invalid_data["traits"] = []

        test_file = temp_config_dir / "invalid.yaml"
        with open(test_file, "w") as f:
            yaml.dump(invalid_data, f)

        # Create valid persona
        valid_file = temp_config_dir / "valid.yaml"
        with open(valid_file, "w") as f:
            yaml.dump(sample_persona_data, f)

        manager = PersonaConfigManager(temp_config_dir)
        manager.load_all_personas()

        issues = manager.validate_all()
        assert "invalid-persona" in issues
        assert "No traits defined" in issues["invalid-persona"]
        assert "test-persona" not in issues

    def test_export_persona(self, manager_with_personas: PersonaConfigManager, temp_config_dir: Path) -> None:
        """Test exporting a persona to YAML."""
        export_path = temp_config_dir / "exported.yaml"
        manager_with_personas.export_persona("test-persona", export_path)

        assert export_path.exists()

        # Load exported file and verify
        with open(export_path, "r") as f:
            exported_data = yaml.safe_load(f)

        assert exported_data["name"] == "Test Persona"
        assert exported_data["slug"] == "test-persona"

    def test_export_persona_not_found(self, manager_with_personas: PersonaConfigManager, temp_config_dir: Path) -> None:
        """Test exporting non-existent persona."""
        export_path = temp_config_dir / "exported.yaml"

        with pytest.raises(PersonaNotFoundError):
            manager_with_personas.export_persona("nonexistent", export_path)

    def test_load_detailed_personas(self, temp_config_dir: Path) -> None:
        """Test loading the actual personas_detailed.yaml file format."""
        personas_file = Path(__file__).parent / "personas_detailed.yaml"
        if personas_file.exists():
            # Copy to temp directory
            import shutil

            shutil.copy(personas_file, temp_config_dir / "personas_detailed.yaml")

            manager = PersonaConfigManager(temp_config_dir)
            personas = manager.load_all_personas()

            # Verify all three personas loaded
            assert len(personas) == 3
            assert "cherry" in personas
            assert "sophia" in personas
            assert "karen" in personas

            # Verify Cherry
            cherry = personas["cherry"]
            assert cherry.name == "Cherry"
            assert cherry.interaction_mode == InteractionMode.ANALYTICAL
            assert len(cherry.traits) == 5
            assert cherry.temperature == 0.4

            # Verify Sophia
            sophia = personas["sophia"]
            assert sophia.name == "Sophia"
            assert sophia.response_style.type == ResponseStyleType.TECHNICAL
            assert sophia.temperature == 0.2

            # Verify Karen
            karen = personas["karen"]
            assert karen.name == "Karen"
            assert karen.response_style.emoji_usage is True
            assert karen.temperature == 0.9
