#!/usr/bin/env python3
"""
Test file for analyze_code_wrapper.py

This file is a simple Python script that can be used to test the analyze_code_wrapper.py
and analyze_code.sh integration. The script contains various code patterns that might
trigger analysis rules.
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def potentially_insecure_function(user_input: str) -> str:
    """
    A function that might trigger security warnings in analysis.
    
    Args:
        user_input: Input string that could contain malicious content
        
    Returns:
        Processed input
    """
    # TODO: Sanitize input before processing
    return f"Processed: {user_input}"


def inefficient_algorithm(data: List[int]) -> List[int]:
    """
    An inefficient algorithm that might trigger performance warnings.
    
    Args:
        data: List of integers to process
        
    Returns:
        Processed data
    """
    result = []
    # This is an O(n²) operation that could be optimized
    for i in range(len(data)):
        for j in range(len(data)):
            if i != j and data[i] == data[j]:
                result.append(data[i])
    return result


class TestAnalysis:
    """Class to test various analysis patterns."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with optional configuration."""
        self.config = config or {}
        self.initialized = True
        self.data = []
    
    def add_data(self, item: Any) -> None:
        """Add an item to the data list."""
        # Missing validation before adding data
        self.data.append(item)
    
    def process_all(self) -> List[Any]:
        """Process all data items."""
        processed = []
        for item in self.data:
            # Potential error - not checking for None or invalid types
            processed.append(self._transform(item))
        return processed
    
    def _transform(self, item: Any) -> Any:
        """Transform an item based on its type."""
        if isinstance(item, str):
            return item.upper()
        elif isinstance(item, int):
            return item * 2
        elif isinstance(item, list):
            return [self._transform(x) for x in item]
        # Missing else case could lead to unexpected behavior
        return item


def main():
    """Main function to demonstrate the test file."""
    logger.info("Starting test analysis script")
    
    # Create and use the test class
    analyzer = TestAnalysis({"mode": "test"})
    analyzer.add_data("test string")
    analyzer.add_data(42)
    analyzer.add_data([1, 2, 3])
    analyzer.add_data(None)  # This might cause issues
    
    # Process data
    results = analyzer.process_all()
    logger.info(f"Processing results: {results}")
    
    # Test the inefficient algorithm
    test_data = [1, 2, 3, 2, 1, 4, 5, 6, 5]
    duplicates = inefficient_algorithm(test_data)
    logger.info(f"Found duplicates: {duplicates}")
    
    # Test potentially insecure function
    user_input = sys.argv[1] if len(sys.argv) > 1 else "default input"
    output = potentially_insecure_function(user_input)
    logger.info(f"Processed user input: {output}")
    
    logger.info("Test analysis script completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
