"""
"""
T = TypeVar("T")

class ToolParameter(BaseModel):
    """
    """
    """
    """
    """
    """
        """
        """
        """
        """
        """
        """
            return_type = type_hints.get("return", Any).__name__

            # Extract parameter information
            parameters = []
            for name, param in sig.parameters.items():
                if name == "self":
                    continue

                param_type = type_hints.get(name, Any).__name__
                required = param.default == inspect.Parameter.empty
                default = None if required else param.default

                # Try to get parameter description from docstring
                param_desc = f"Parameter {name}"

                parameters.append(
                    ToolParameter(
                        name=name,
                        type_hint=param_type,
                        description=param_desc,
                        required=required,
                        default=default,
                    )
                )

            self._metadata = ToolMetadata(
                name=self.name,
                description=self.description,
                parameters=parameters,
                return_type=return_type,
                requires_async=inspect.iscoroutinefunction(self.execute),
            )

        return self._metadata

    def create_input_model(self) -> Type[BaseModel]:
        """
        """
        model_name = f"{self.name.title()}Input"
        return create_model(model_name, **fields)

class ToolRegistry:
    """
    """
        """Initialize the tool registry."""
        """
        """
            raise ValueError(f"Tool with name '{tool.name}' is already registered")

        self._tools[tool.name] = tool

        # Register categories
        if categories:
            for category in categories:
                if category not in self._categories:
                    self._categories[category] = set()
                self._categories[category].add(tool.name)

        logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Tool:
        """
        """
            raise ValueError(f"No tool with name '{name}' is registered")

        return self._tools[name]

    def get_tools_by_category(self, category: str) -> List[Tool]:
        """
        """
        """
        """
        """
        """
    """
    """
        """
        """
        """
        """
            raise ValueError(f"Tool with name '{tool.name}' is already added")

        self.tools.append(tool)
        self._tool_map[tool.name] = tool

    def remove_tool(self, tool_name: str) -> None:
        """
        """
            raise ValueError(f"No tool with name '{tool_name}' is added")

        tool = self._tool_map[tool_name]
        self.tools.remove(tool)
        del self._tool_map[tool_name]

    def has_tool(self, tool_name: str) -> bool:
        """
        """
        """
        """
                "name": tool.name,
                "description": tool.description,
                "parameters": [p.dict() for p in tool.get_metadata().parameters],
            }
            for tool in self.tools
        ]

    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        """
        """
            raise ValueError(f"Tool {tool_name} not found")

        tool = self._tool_map[tool_name]

        # Create and validate input model
        input_model = tool.create_input_model()
        validated_inputs = input_model(**kwargs).dict()

        # Execute the tool
        result = await tool.execute(**validated_inputs)

        return result

# Global tool registry
_global_registry = ToolRegistry()

def get_tool_registry() -> ToolRegistry:
    """
    """