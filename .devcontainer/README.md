# Dev Container

This dev container provides a reproducible environment for working on Cherry AI.

## Features
- Python 3.10 with common tools
- Node.js 20 with PNPM
- Pulumi CLI for infrastructure management

## Usage
1. Open the repository in VS Code with the Remote Containers extension.
2. Reopen in container when prompted.
3. Run `pnpm install` and `pip install -r requirements/base.txt` to set up dependencies.

The container includes Docker and Git utilities for local testing and CI parity.
