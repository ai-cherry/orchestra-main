# Orchestra Configuration Management Standards

This document outlines the standards and best practices for configuration management in the Orchestra project.

## Table of Contents

- [Environment Variable Management](#environment-variable-management)
- [Secret Management](#secret-management)
- [Configuration Files](#configuration-files)
- [Pulumi Infrastructure](#pulumi-infrastructure)
- [Naming Conventions](#naming-conventions)
- [Migration Guide](#migration-guide)

## Environment Variable Management

### Key Principles

1. **Dual-mode Support**:

   - Environment variables are supported via both `.env` files and    - Environment variables take precedence over
2. **Placement Guidelines**:

   - `.env` file: Development-only variables, non-sensitive configuration
   -
3. **Type Separation**:
   - Configuration values: `.env` file or YAML configuration
   - Secrets: Should be properly secured in
### Standard Environment Variables

| Category        | Environment Variable            | Pulumi/| --------------- | ------------------------------- | ----------------------------- | --------------------------------------------------- |
| **Environment** | `ENVIRONMENT`                   | `env`                         | Environment name (development, staging, production) |
| **| **Database**    | `POSTGRES_HOST`                 | N/A                           | PostgreSQL host address                             |
|                 | `POSTGRES_DATABASE`             | N/A                           | PostgreSQL database name                            |
|                 | `POSTGRES_USER`                 | N/A                           | PostgreSQL username                                 |
|                 | `POSTGRES_PASSWORD_SECRET_NAME` | `postgres-password-[env]`     | Secret name for PostgreSQL password                 |
| **Redis**       | `REDIS_HOST`                    | N/A                           | Redis host address                                  |
|                 | `REDIS_PORT`                    | N/A                           | Redis port                                          |
|                 | `REDIS_PASSWORD_SECRET_NAME`    | `redis-auth-[env]`            | Secret name for Redis password                      |
| **API Keys**    | `[SERVICE]_API_KEY`             | `[service]-api-key-[env]`     | Direct service API key (dev only)                   |
|                 | `[SERVICE]_API_KEY_SECRET_NAME` | N/A                           | Secret name reference (production)                  |

## Secret Management

### Dual Access Pattern

```python
# Using the new from config.secret_manager import get_secret, secrets

# Option 1: Function call
api_key = get_secret("openai-api-key")

# Option 2: Dictionary-like access
api_key = secrets["openai-api-key"]

# Option 3: With default fallback
api_key = secrets.get("openai-api-key", "default-value")
```

### Adding New Secrets

1. **Add to `.env`** for development (temporarily)
2. **Add to `add_secrets_to_manager.sh`** for migration to 3. **Add to `secrets.py`** for Pulumi management
4. **Update code** to use the
### Secret Naming Convention

- **
  - Example: `openai-api-key-production`

- **Environment Variable**: `SERVICE_NAME_PURPOSE`
  - Example: `OPENAI_API_KEY`

## Configuration Files

### YAML Configuration

- `config/personas.yaml`: Persona definitions with prompt templates
- `config/application.yaml`: Application-wide static configuration

### Python Configuration

- `config/settings.py`: Main settings class with Pydantic model
- `config/loader.py`: Configuration loading utilities
- `config/secret_manager.py`: Secret access utilities

## Pulumi Infrastructure

### Resource Organization

- `main.py`: Core infrastructure setup
- `cloudrun.py`: - `cloudsql.py`: Database configuration
- `network.py`: Networking configuration
- `secrets.py`:
### Secret Integration

Pulumi integrates secrets in two ways:

1. **Resource Creation**:

   ```pulumi
   llm_api_keys = google_secret_manager_secret( {
     for_each = { ... }
     secret_id = "${each.key}-${var.env}"
     ...
   }
   ```

2. **Resource Access in    ```pulumi
   env {
     name = "OPENAI_API_KEY"
     value_source {
       secret_key_ref {
         secret = google_secret_manager_secret.llm_api_keys["openai-api-key"].id
         version = "latest"
       }
     }
   }
   ```

## Naming Conventions

### File Extensions

- `.yaml` or `.yml`: YAML configuration files
- `.py`: Python source code (including Pulumi)
- `.sh`: Shell scripts
- `.py`: Python source code
- `.env`: Environment variable files (not checked into git)
- `.env.example`: Example environment variable file (checked into git)

### Configuration Keys

- **YAML**: `lower_snake_case` for keys
- **Environment Variables**: `UPPER_SNAKE_CASE`
- **Pulumi Resources**: `lower_snake_case`
- **
## Migration Guide

### Step 1: Setup
1. Add the `secret_manager.py` utility to your project
2. Ensure `google-cloud-secret-manager` is in your requirements

### Step 2: Copy Secrets to
```bash
# Make the script executable
chmod +x add_secrets_to_manager.sh

# Run the script (requires ./add_secrets_to_manager.sh
```

### Step 3: Update Pulumi

```bash
# Navigate to Pulumi directory
cd infra/orchestra-pulumi

# Initialize Pulumi
pulumi init

# Apply changes
pulumi apply
```

### Step 4: Update Code to Use
```python
# Old way
api_key = os.environ.get("OPENAI_API_KEY")

# New way
from config.secret_manager import secrets
api_key = secrets["openai-api-key"]
```

## Conclusion

Following these configuration standards will ensure:

1. Consistent naming across the project
2. Secure handling of sensitive information
3. Backward compatibility with existing code
4. Clear separation of concerns between configuration types

For questions or improvements to these standards, please file an issue or pull request.

### Persona Memory Variables

The persona memory system uses separate Redis databases and PostgreSQL schemas for each persona. Example variables:

```
REDIS_DB_CHERRY=0
REDIS_DB_SOPHIA=1
REDIS_DB_KAREN=2
POSTGRES_SCHEMA_CHERRY=cherry
POSTGRES_SCHEMA_SOPHIA=sophia
POSTGRES_SCHEMA_KAREN=karen
NEO4J_URL=bolt://localhost:7687
```

