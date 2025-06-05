#!/usr/bin/env python3
"""
Test script for the Orchestra AI Assistant
"""

def calculate_fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number.
    
    This is intentionally inefficient for testing.
    """
    if n <= 1:
        return n
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)

def process_data(data):
    """Process some data without proper error handling."""
    result = []
    for item in data:
        # No type checking
        processed = item * 2
        result.append(processed)
    return result

class DataManager:
    """A simple data manager that could use better design."""
    
    def __init__(self):
        self.data = []
    
    def add(self, item):
        self.data.append(item)
    
    def get_all(self):
        return self.data
    
    def clear(self):
        self.data = []

# Example usage
if __name__ == "__main__":
    # Test Fibonacci
    print(f"Fib(10) = {calculate_fibonacci(10)}")
    
    # Test data processing
    numbers = [1, 2, 3, 4, 5]
    doubled = process_data(numbers)
    print(f"Doubled: {doubled}")
    
    # Test DataManager
    dm = DataManager()
    dm.add("item1")
    dm.add("item2")
    print(f"Data: {dm.get_all()}") 