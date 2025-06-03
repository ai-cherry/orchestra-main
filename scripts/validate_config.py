#!/usr/bin/env python3
"""
"""
    "type": "object",
    "properties": {
        "orchestrator": {
            "type": "object",
            "properties": {
                "workflow_timeout": {"type": "integer", "minimum": 60},
                "max_parallel_tasks": {"type": "integer", "minimum": 1},
                "checkpoint_interval": {"type": "integer", "minimum": 30}
            },
            "required": ["workflow_timeout", "max_parallel_tasks"]
        },
        "agents": {
            "type": "object",
            "properties": {
                "eigencode": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "timeout": {"type": "integer", "minimum": 60},
                        "retry_attempts": {"type": "integer", "minimum": 0}
                    }
                },
                "cursor_ai": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "timeout": {"type": "integer", "minimum": 60},
                        "retry_attempts": {"type": "integer", "minimum": 0}
                    }
                },
                "roo_code": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "timeout": {"type": "integer", "minimum": 60},
                        "retry_attempts": {"type": "integer", "minimum": 0}
                    }
                }
            }
        },
        "mcp_server": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "format": "uri"},
                "health_check_interval": {"type": "integer", "minimum": 10}
            },
            "required": ["url"]
        },
        "database": {
            "type": "object",
            "properties": {
                "connection_pool_size": {"type": "integer", "minimum": 1},
                "query_timeout": {"type": "integer", "minimum": 1}
            }
        },
        "weaviate": {
            "type": "object",
            "properties": {
                "batch_size": {"type": "integer", "minimum": 1},
                "timeout": {"type": "integer", "minimum": 1}
            }
        },
        "logging": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                "max_file_size": {"type": "string"},
                "backup_count": {"type": "integer", "minimum": 1}
            }
        }
    },
    "required": ["orchestrator", "agents", "mcp_server"]
}

def validate_yaml_config(config_path: Path) -> bool:
    """Validate YAML configuration file"""
        print(f"✓ Configuration file {config_path} is valid")
        return True
    except Exception:

        pass
        print(f"✗ Configuration file {config_path} not found")
        return False
    except Exception:

        pass
        print(f"✗ YAML parsing error in {config_path}: {e}")
        return False
    except Exception:

        pass
        print(f"✗ Configuration validation error in {config_path}: {e.message}")
        return False

def validate_workflow_config(config_path: Path) -> bool:
    """Validate workflow configuration JSON"""
        "type": "object",
        "properties": {
            "workflow_id": {"type": "string"},
            "description": {"type": "string"},
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "agent": {"type": "string", "enum": ["analyzer", "implementer", "refiner"]},
                        "inputs": {"type": "object"},
                        "dependencies": {"type": "array", "items": {"type": "string"}},
                        "priority": {"type": "integer"}
                    },
                    "required": ["id", "name", "agent"]
                }
            }
        },
        "required": ["workflow_id", "tasks"]
    }
    
    try:

    
        pass
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        validate(config, workflow_schema)
        print(f"✓ Workflow configuration {config_path} is valid")
        return True
    except Exception:

        pass
        print(f"✗ Workflow configuration {config_path} not found")
        return False
    except Exception:

        pass
        print(f"✗ JSON parsing error in {config_path}: {e}")
        return False
    except Exception:

        pass
        print(f"✗ Workflow validation error in {config_path}: {e.message}")
        return False

def main():
    """Main validation function"""
    print("AI Orchestrator Configuration Validation")
    print("=" * 40)
    
    # Base directory
    base_dir = Path(__file__).parent.parent
    
    # Validate main configuration
    config_file = base_dir / "ai_components" / "configs" / "orchestrator_config.yaml"
    config_valid = validate_yaml_config(config_file)
    
    # Validate example workflow
    workflow_file = base_dir / "ai_components" / "configs" / "example_workflow.json"
    workflow_valid = validate_workflow_config(workflow_file)
    
    # Check for required environment variables
    print("\nChecking environment variables...")
    required_env_vars = [
        "POSTGRES_HOST",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "WEAVIATE_URL",
        "WEAVIATE_API_KEY"
    ]
    
    env_valid = True
    for var in required_env_vars:
        if os.environ.get(var):
            print(f"✓ {var} is set")
        else:
            print(f"✗ {var} is not set")
            env_valid = False
    
    # Overall result
    print("\n" + "=" * 40)
    if config_valid and workflow_valid and env_valid:
        print("✓ All validations passed")
        sys.exit(0)
    else:
        print("✗ Validation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()