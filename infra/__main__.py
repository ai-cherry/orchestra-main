#!/usr/bin/env python3
"""
Main entry point for Pulumi infrastructure deployment.
"""

# Import the stack to register resources
import vultr_single_node_stack  # noqa: F401

if __name__ == "__main__":
    # Pulumi will handle the rest
    pass
