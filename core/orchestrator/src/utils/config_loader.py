"""
"""
T = TypeVar("T", bound=BaseModel)

class ConfigLoader(Generic[T]):
    """
    """
        env_prefix: str = "",
        auto_create_config: bool = False,
        default_config_values: Dict[str, Any] = None,
    ):
        """
        """
        self.env_prefix = env_prefix.upper() + "_" if env_prefix else ""
        self.auto_create_config = auto_create_config
        self.default_config_values = default_config_values or {}

        # Cached config
        self._config: Optional[T] = None

    @error_boundary(propagate_types=[ConfigurationError])
    def load_config(self, reload: bool = False) -> T:
        """
        """
                logger.warning(f"Error loading config from {file_path}: {str(e)}")

                # Create default config file if enabled
                if self.auto_create_config and not os.path.exists(file_path):
                    try:

                        pass
                        self._create_default_config_file(file_path)
                    except Exception:

                        pass
                        logger.warning(f"Error creating default config file at {file_path}: {str(create_error)}")

        # Override with environment variables
        env_config = self._load_from_env_vars()
        config_data.update(env_config)

        # Validate configuration with the model
        try:

            pass
            validated_config = self.config_class(**config_data)
            self._config = validated_config
            return validated_config
        except Exception:

            pass
            error_msg = f"Configuration validation failed: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg, original_error=e)

    def _load_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        """
            return {}

        file_extension = os.path.splitext(file_path)[1].lower()

        try:


            pass
            with open(file_path, "r") as f:
                if file_extension in [".yaml", ".yml"]:
                    return yaml.safe_load(f) or {}
                elif file_extension == ".json":
                    return json.load(f)
                else:
                    logger.warning(f"Unsupported file extension for config: {file_extension}")
                    return {}
        except Exception:

            pass
            logger.error(f"Error reading config file {file_path}: {str(e)}")
            raise ConfigurationError(f"Failed to read config file {file_path}", original_error=e)

    def _load_from_env_vars(self) -> Dict[str, Any]:
        """
        """
        model_fields = self.config_class.__fields__ if hasattr(self.config_class, "__fields__") else {}

        for field_name, field in model_fields.items():
            # Convert from snake_case to UPPER_SNAKE_CASE with prefix
            env_var_name = f"{self.env_prefix}{field_name.upper()}"

            if env_var_name in os.environ:
                env_value = os.environ[env_var_name]

                # Convert to appropriate type (basic string/int/float/bool)
                if field.type_ == bool:
                    env_config[field_name] = env_value.lower() in [
                        "true",
                        "yes",
                        "y",
                        "1",
                    ]
                elif field.type_ == int:
                    env_config[field_name] = int(env_value)
                elif field.type_ == float:
                    env_config[field_name] = float(env_value)
                else:
                    env_config[field_name] = env_value

        return env_config

    def _create_default_config_file(self, file_path: str) -> None:
        """
        """
        with open(file_path, "w") as f:
            if file_extension in [".yaml", ".yml"]:
                yaml.dump(data, f, default_flow_style=False)
            elif file_extension == ".json":
                json.dump(data, f, indent=2)
            else:
                # Just write as JSON if extension not recognized
                json.dump(data, f, indent=2)

        logger.info(f"Created default config file at {file_path}")

    def get_config(self) -> T:
        """
        """
    """
    """
        os.path.join(os.getcwd(), "config/default.yaml"),
        os.path.join(os.getcwd(), "phi_config.yaml"),
        os.environ.get("ORCHESTRA_CONFIG_PATH", ""),
    ]

    # Filter out empty paths
    config_paths = [p for p in config_paths if p]

    return ConfigLoader(
        config_class=Settings,
        config_file_paths=config_paths,
        env_prefix="ORCHESTRA",
        auto_create_config=False,
    )

def get_app_config() -> Any:
    """
    """
    """
    """
    module_path = module_name.replace(".", "/")
    config_paths = [
        os.path.join(os.getcwd(), f"config/{module_path}.yaml"),
        os.path.join(os.getcwd(), f"config/{module_path}.json"),
        os.environ.get(f"{module_name.upper()}_CONFIG_PATH", ""),
    ]

    # Filter out empty paths
    config_paths = [p for p in config_paths if p]

    loader = ConfigLoader(
        config_class=config_class,
        config_file_paths=config_paths,
        env_prefix=module_name.upper(),
        auto_create_config=True,
        default_config_values=default_config or {},
    )

    return loader.get_config()
