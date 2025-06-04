import json
import os

CONFIG_ROOTS = ["config", "./", "infra", "conductor", "core", "mcp_server"]
config_files = []
env_files = []

for root in CONFIG_ROOTS:
    for dirpath, dirnames, filenames in os.walk(root):
        for fname in filenames:
            path = os.path.join(dirpath, fname)
            if fname.endswith((".yaml", ".yml", ".json")):
                config_files.append(path)
            elif fname.startswith(".env") or "env" in fname.lower():
                env_files.append(path)

inventory = {
    "config_files": config_files,
    "env_files": env_files,
}

print(json.dumps(inventory, indent=2))
