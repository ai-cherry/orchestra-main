"""
"""
    "slack": SlackParser,
    "zip": ZipHandler,
}

def get_parser(source_type: str) -> Type[ParserInterface]:
    """
    """
        raise ValueError(f"Unsupported source type: {source_type}")
    return parser_class

__all__ = [
    "SlackParser",
    "ZipHandler",
    "get_parser",
    "PARSER_REGISTRY",
]