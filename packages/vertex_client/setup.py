#!/usr/bin/env python3
"""
Setup script for the Vertex Client package.
"""

import os

from setuptools import find_packages, setup

# Get long description from README
here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Orchestra Vertex AI Agent Manager"

# Read requirements from requirements.txt
with open(os.path.join(here, "requirements.txt"), encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="orchestra-vertex-client",
    version="0.1.0",
    description="Orchestra Vertex AI Agent Manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Orchestra Team",
    author_email="info@orchestra.ai",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="vertex-ai, google-cloud, orchestration, automation",
    packages=find_packages(include=["vertex_client", "vertex_client.*"]),
    python_requires=">=3.10, <4",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "vertex-cli=vertex_client.cli:main",
        ],
    },
)
