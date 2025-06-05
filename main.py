#!/usr/bin/env python3
"""
Live Collaboration Test Project
This file will be monitored by Manus AI in real-time!
"""

def greet_manus():
    """Say hello to Manus AI through live collaboration"""
    return "Hello Manus! You can see this code in real-time! 🚀"

def fibonacci(n):
    """Calculate fibonacci number - Manus can see changes instantly"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    """Main function - any changes here appear instantly to Manus"""
    print(greet_manus())
    
    # Test fibonacci
    for i in range(10):
        result = fibonacci(i)
        print(f"fibonacci({i}) = {result}")

if __name__ == "__main__":
    main()

