"""
Parser implementations for various data sources.

This module contains concrete parser implementations for each supported
data source including Slack, Gong.io, Salesforce, Looker, and HubSpot.
"""

from typing import Dict, Type
from ..interfaces.parser import ParserInterface

# Import concrete parsers
from .slack_parser import SlackParser
from .zip_handler import ZipHandler

# Parser registry mapping source types to parser classes
PARSER_REGISTRY: Dict[str, Type[ParserInterface]] = {
    "slack": SlackParser,
    "zip": ZipHandler,
}

def get_parser(source_type: str) -> Type[ParserInterface]:
    """
    Get the parser class for a given source type.
    
    Args:
        source_type: The type of data source
        
    Returns:
        The parser class for the source type
        
    Raises:
        ValueError: If source type is not supported
    """
    parser_class = PARSER_REGISTRY.get(source_type.lower())
    if not parser_class:
        raise ValueError(f"Unsupported source type: {source_type}")
    return parser_class

__all__ = [
    "SlackParser",
    "ZipHandler",
    "get_parser",
    "PARSER_REGISTRY",
]