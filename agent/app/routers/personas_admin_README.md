# Personas Admin API

The Personas Admin API provides endpoints for managing persona configurations in the Orchestra AI system. This API allows administrators to list, retrieve, update, validate, and export persona configurations.

## Overview

The Personas Admin API is built on FastAPI and integrates with the `PersonaConfigManager` to provide a RESTful interface for persona management. All endpoints require API key authentication.

## Authentication

All endpoints require an `X-API-Key` header with a valid API key:

```bash
X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd
```

## Endpoints

### List Personas

```http
GET /api/personas/
```

List all available personas with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by persona status (active, inactive, draft, archived)
- `tags` (optional): Comma-separated list of tags to filter by

**Response:**
```json
{
  "personas": [...],
  "total": 10,
  "filtered": 5
}
```

### Get Persona

```http
GET /api/personas/{slug}
```

Retrieve a specific persona by its slug identifier.

**Path Parameters:**
- `slug`: The unique slug identifier of the persona

**Response:**
```json
{
  "id": "uuid",
  "name": "Technical Architect",
  "slug": "technical-architect",
  "description": "Expert in system design...",
  "status": "active",
  ...
}
```

### Update Persona

```http
PUT /api/personas/{slug}
```

Update a persona's configuration. Note: This updates the in-memory configuration only. To persist changes, use the export endpoint.

**Path Parameters:**
- `slug`: The unique slug identifier of the persona

**Request Body:**
```json
{
  "status": "active",
  "temperature": 0.7,
  "tags": ["updated", "technical"],
  "is_public": true
}
```

**Response:** Updated persona configuration

### Reload Persona

```http
POST /api/personas/{slug}/reload
```

Reload a persona from its configuration file, discarding any in-memory changes.

**Path Parameters:**
- `slug`: The unique slug identifier of the persona

**Response:** Reloaded persona configuration

### Validate All Personas

```http
GET /api/personas/validate/all
```

Validate all loaded personas and return a validation report.

**Response:**
```json
{
  "valid": true,
  "issues": {
    "persona-slug": ["issue1", "issue2"]
  },
  "total_personas": 10,
  "personas_with_issues": 2
}
```

### Export Persona

```http
POST /api/personas/{slug}/export
```

Export a persona configuration to a YAML file.

**Path Parameters:**
- `slug`: The unique slug identifier of the persona

**Request Body:**
```json
{
  "output_path": "/path/to/export/persona.yaml"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Persona 'technical-architect' exported successfully",
  "output_path": "/path/to/export/persona.yaml",
  "slug": "technical-architect"
}
```

### Check for Updates

```http
POST /api/personas/check-updates
```

Check for updated persona files and reload any that have changed.

**Response:**
```json
{
  "status": "success",
  "updated_count": 2,
  "updated_personas": ["persona1", "persona2"],
  "message": "Checked for updates, 2 personas reloaded"
}
```

### Health Check

```http
GET /api/personas/health/status
```

Check the health status of the personas admin service.

**Response:**
```json
{
  "status": "healthy",
  "service": "personas-admin",
  "personas_loaded": 10,
  "config_dir": "/config/personas",
  "manager_initialized": true
}
```

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages:

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid or missing API key
- `404 Not Found`: Persona not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

Error Response Format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Integration with PersonaConfigManager

The API integrates with the `PersonaConfigManager` class from `core.personas.manager`, which provides:

- Loading persona configurations from YAML files
- Caching and hot-reloading support
- Validation of persona configurations
- Export functionality

## Configuration

The personas configuration directory is set via the `PERSONAS_CONFIG_DIR` constant in the router module. By default, it points to `config/personas`.

## Usage Examples

### List Active Personas with Specific Tags

```bash
curl -X GET "http://localhost:8000/api/personas/?status=active&tags=technical,expert" \
  -H "X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd"
```

### Update a Persona's Temperature Setting

```bash
curl -X PUT "http://localhost:8000/api/personas/technical-architect" \
  -H "X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd" \
  -H "Content-Type: application/json" \
  -d '{"temperature": 0.3}'
```

### Export a Persona Configuration

```bash
curl -X POST "http://localhost:8000/api/personas/technical-architect/export" \
  -H "X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd" \
  -H "Content-Type: application/json" \
  -d '{"output_path": "/exports/technical-architect.yaml"}'
```

## Testing

The API includes comprehensive unit and integration tests in `agent/tests/test_personas_admin.py`. Run tests with:

```bash
pytest agent/tests/test_personas_admin.py -v
```

For integration tests:
```bash
pytest agent/tests/test_personas_admin.py -v -m integration
```

## Performance Considerations

- The PersonaConfigManager caches loaded personas in memory
- File modification times are tracked for efficient hot-reloading
- All endpoints use async/await for non-blocking I/O operations
- The API supports concurrent requests with proper error isolation

## Security

- API key authentication is required for all endpoints except health check
- Input validation is performed on all request parameters
- File paths in export operations should be validated to prevent directory traversal
- Consider implementing rate limiting for production deployments

## Future Enhancements

1. Add pagination support for listing large numbers of personas
2. Implement persona versioning and rollback functionality
3. Add bulk operations for updating multiple personas
4. Integrate with a persistent storage backend for configuration changes
5. Add WebSocket support for real-time persona updates
6. Implement fine-grained access control per persona