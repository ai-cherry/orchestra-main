import json
import os

ROOTS = [
    "mcp_server",
    "tools",
    "scripts",
    "orchestra_system",
    "ai-orchestra",
    "orchestrator",
    "packages",
    "core",
]

inventory = {
    "python_modules": [],
    "cli_scripts": [],
    "adapters": [],
}

for root in ROOTS:
    for dirpath, dirnames, filenames in os.walk(root):
        for fname in filenames:
            path = os.path.join(dirpath, fname)
            if fname.endswith(".py"):
                inventory["python_modules"].append(path)
                if "adapter" in fname or "Adapter" in fname:
                    inventory["adapters"].append(path)
                if (
                    os.access(path, os.X_OK)
                    or path.startswith("scripts/")
                    or path.startswith("tools/")
                ):
                    inventory["cli_scripts"].append(path)
            elif fname.endswith(".sh") or fname.endswith(".bash"):
                inventory["cli_scripts"].append(path)

print(json.dumps(inventory, indent=2))
