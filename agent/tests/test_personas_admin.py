"""
"""
    """Create a mock persona configuration for testing."""
        name="Test Persona",
        slug="test-persona",
        description="A test persona for unit testing",
        status=PersonaStatus.ACTIVE,
        traits=[
            PersonaTrait(
                name="analytical",
                category=TraitCategory.COGNITIVE,
                value=85,
                weight=2.0,
            )
        ],
        response_style=ResponseStyle(
            type=ResponseStyleType.TECHNICAL,
            tone="professional",
            formality_level=8,
            verbosity=6,
        ),
        interaction_mode=InteractionMode.ANALYTICAL,
        created_by="test@example.com",
        tags=["test", "mock"],
    )

@pytest.fixture
def mock_persona_manager(mock_persona_config: PersonaConfiguration) -> MagicMock:
    """Create a mock PersonaConfigManager."""
    manager.personas = {"test-persona": mock_persona_config}
    manager.get_persona.return_value = mock_persona_config
    manager.list_personas.return_value = [mock_persona_config]
    manager.validate_all.return_value = {}
    manager.check_for_updates.return_value = set()
    return manager

@pytest.fixture
def test_client(mock_persona_manager: MagicMock) -> TestClient:
    """Create a test client with mocked dependencies."""
    with patch("agent.app.routers.personas_admin.get_persona_manager") as mock_get_manager:
        mock_get_manager.return_value = mock_persona_manager

        # Import here to ensure patches are applied
        from agent.app.main import app

        client = TestClient(app)
        yield client

@pytest.fixture
def valid_api_key() -> str:
    """Return the valid API key for testing."""
    return "4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd"

class TestPersonasAdminRouter:
    """Test cases for the personas admin router."""
        """Test successful listing of personas."""
        response = test_client.get("/api/personas/", headers={"X-API-Key": valid_api_key})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "personas" in data
        assert "total" in data
        assert "filtered" in data
        assert len(data["personas"]) == 1
        assert data["personas"][0]["slug"] == "test-persona"

    def test_list_personas_with_filters(
        self, test_client: TestClient, valid_api_key: str, mock_persona_manager: MagicMock
    ) -> None:
        """Test listing personas with status and tag filters."""
        response = test_client.get("/api/personas/?status=active&tags=test,mock", headers={"X-API-Key": valid_api_key})

        assert response.status_code == status.HTTP_200_OK
        # Verify the manager was called with correct filters
        mock_persona_manager.list_personas.assert_called_with(status=PersonaStatus.ACTIVE, tags=["test", "mock"])

    def test_list_personas_unauthorized(self, test_client: TestClient) -> None:
        """Test listing personas without valid API key."""
        response = test_client.get("/api/personas/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = test_client.get("/api/personas/", headers={"X-API-Key": "invalid-key"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_persona_success(
        self, test_client: TestClient, valid_api_key: str, mock_persona_config: PersonaConfiguration
    ) -> None:
        """Test successful retrieval of a specific persona."""
        response = test_client.get("/api/personas/test-persona", headers={"X-API-Key": valid_api_key})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["slug"] == "test-persona"
        assert data["name"] == "Test Persona"

    def test_get_persona_not_found(
        self, test_client: TestClient, valid_api_key: str, mock_persona_manager: MagicMock
    ) -> None:
        """Test getting a non-existent persona."""
        mock_persona_manager.get_persona.side_effect = PersonaNotFoundError("Persona not found")

        response = test_client.get("/api/personas/non-existent", headers={"X-API-Key": valid_api_key})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

    def test_update_persona_success(
        self, test_client: TestClient, valid_api_key: str, mock_persona_config: PersonaConfiguration
    ) -> None:
        """Test successful persona update."""
        update_data = {"status": "inactive", "temperature": 0.5, "tags": ["updated", "test"]}

        response = test_client.put("/api/personas/test-persona", headers={"X-API-Key": valid_api_key}, json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["slug"] == "test-persona"

    def test_update_persona_validation_error(self, test_client: TestClient, valid_api_key: str) -> None:
        """Test persona update with invalid data."""
        update_data = {"temperature": 3.0}  # Out of range

        response = test_client.put("/api/personas/test-persona", headers={"X-API-Key": valid_api_key}, json=update_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_reload_persona_success(
        self, test_client: TestClient, valid_api_key: str, mock_persona_manager: MagicMock
    ) -> None:
        """Test successful persona reload."""
        mock_persona_manager.reload_persona.return_value = mock_persona_manager.personas["test-persona"]

        response = test_client.post("/api/personas/test-persona/reload", headers={"X-API-Key": valid_api_key})

        assert response.status_code == status.HTTP_200_OK
        mock_persona_manager.reload_persona.assert_called_once_with("test-persona")

    def test_validate_all_personas_success(self, test_client: TestClient, valid_api_key: str) -> None:
        """Test successful validation of all personas."""
        response = test_client.get("/api/personas/validate/all", headers={"X-API-Key": valid_api_key})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True
        assert data["total_personas"] == 1
        assert data["personas_with_issues"] == 0

    def test_validate_all_personas_with_issues(
        self, test_client: TestClient, valid_api_key: str, mock_persona_manager: MagicMock
    ) -> None:
        """Test validation when personas have issues."""
            "test-persona": ["No traits defined", "Empty model preferences list"]
        }

        response = test_client.get("/api/personas/validate/all", headers={"X-API-Key": valid_api_key})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is False
        assert data["personas_with_issues"] == 1
        assert "test-persona" in data["issues"]

    def test_export_persona_success(
        self, test_client: TestClient, valid_api_key: str, mock_persona_manager: MagicMock, tmp_path: Path
    ) -> None:
        """Test successful persona export."""
        export_path = tmp_path / "exported_persona.yaml"

        response = test_client.post(
            "/api/personas/test-persona/export",
            headers={"X-API-Key": valid_api_key},
            json={"output_path": str(export_path)},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["slug"] == "test-persona"
        mock_persona_manager.export_persona.assert_called_once()

    def test_check_for_updates_success(
        self, test_client: TestClient, valid_api_key: str, mock_persona_manager: MagicMock
    ) -> None:
        """Test checking for persona updates."""
        mock_persona_manager.check_for_updates.return_value = {"updated-persona"}

        response = test_client.post("/api/personas/check-updates", headers={"X-API-Key": valid_api_key})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["updated_count"] == 1
        assert "updated-persona" in data["updated_personas"]

    def test_health_check_success(self, test_client: TestClient, mock_persona_manager: MagicMock) -> None:
        """Test health check endpoint."""
        response = test_client.get("/api/personas/health/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "personas-admin"
        assert data["personas_loaded"] == 1

    def test_manager_initialization_error(self, test_client: TestClient, valid_api_key: str) -> None:
        """Test handling of PersonaConfigManager initialization errors."""
        with patch("agent.app.routers.personas_admin.PersonaConfigManager") as mock_manager_class:
            mock_manager_class.side_effect = PersonaConfigError("Config directory error")

            # Reset the global manager to force re-initialization
            import agent.app.routers.personas_admin

            agent.app.routers.personas_admin.persona_manager = None

            response = test_client.get("/api/personas/", headers={"X-API-Key": valid_api_key})

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to initialize persona manager" in response.json()["detail"]

class TestPersonasAdminIntegration:
    """Integration tests for personas admin router."""
        """Test complete persona lifecycle: list, get, update, export."""
        headers = {"X-API-Key": valid_api_key}

        # List personas
        response = test_client.get("/api/personas/", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        initial_count = response.json()["total"]

        # Get specific persona
        response = test_client.get("/api/personas/test-persona", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        original_persona = response.json()

        # Update persona
        update_data = {"temperature": 0.9, "tags": ["integration-test"]}
        response = test_client.put("/api/personas/test-persona", headers=headers, json=update_data)
        assert response.status_code == status.HTTP_200_OK

        # Export persona
        export_path = tmp_path / "integration_test_persona.yaml"
        response = test_client.post(
            "/api/personas/test-persona/export", headers=headers, json={"output_path": str(export_path)}
        )
        assert response.status_code == status.HTTP_200_OK

        # Validate all
        response = test_client.get("/api/personas/validate/all", headers=headers)
        assert response.status_code == status.HTTP_200_OK
