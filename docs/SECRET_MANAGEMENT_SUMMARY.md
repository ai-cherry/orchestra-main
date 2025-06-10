# Secret Management Overview

All credentials for Orchestra AI are stored via **Pulumi** and loaded into the application at runtime. Secrets are never committed to the repository.

1. Run `python scripts/generate_env_from_pulumi.py` to create a local `.env` file.
2. Source the file with `source .env` before using any automation scripts or Cursor IDE.
3. Update secrets in Pulumi using `pulumi config set --secret <name> <value>`.

Cursor IDE uses Model Context Protocol (MCP) servers to access infrastructure APIs. The IDE reads required keys from the environment, so once `.env` is loaded, Cursor can perform authorized changes across your stack.
