from setuptools import setup, find_packages

setup(
    name="mcp-server",
    version="0.1.0",
    description="Model Context Protocol (MCP) Memory System",
    author="AI Orchestra Team",
    author_email="info@example.com",
    packages=find_packages(),
    install_requires=[
        "flask>=2.0.0",
        "flask-cors>=3.0.0",
        "flask-socketio>=5.0.0",
        "requests>=2.25.0",
        "aiohttp>=3.7.0",
        "pydantic>=1.8.0"
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        "console_scripts": [
            "mcp-server=mcp_server.main:main",
        ],
    },
)
