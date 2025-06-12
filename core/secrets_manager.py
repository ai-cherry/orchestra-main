#!/usr/bin/env python3
"""
Unified Secrets Manager for Orchestra AI
- Loads secrets from environment, .env, or (optionally) encrypted file
- Provides get_secret, validate, rotate, and CLI
- Caches secrets in memory
- Usable by all personas, Cursor AI, infra, and backend
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict
import json

class SecretsManager:
    def __init__(self, env_file: Optional[str] = None):
        self._cache: Dict[str, str] = {}
        self.env_file = env_file or str(Path(os.getcwd()) / ".env")
        self._load_env_file()

    def _load_env_file(self):
        if not os.path.exists(self.env_file):
            return
        try:
            with open(self.env_file, "r") as f:
                for line in f:
                    if line.strip() and not line.strip().startswith("#"):
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            self._cache[k.strip()] = v.strip().strip('"\'')
        except Exception as e:
            print(f"[SecretsManager] Error loading .env: {e}")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        # Priority: env > cache > default
        return os.getenv(key) or self._cache.get(key) or default

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.get(key, default)

    def validate(self, required: list) -> Dict[str, bool]:
        results = {}
        for key in required:
            results[key] = bool(self.get(key))
        return results

    def rotate(self, key: str, new_value: str):
        # Update in .env file
        lines = []
        found = False
        if os.path.exists(self.env_file):
            with open(self.env_file, "r") as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={new_value}\n"
                    found = True
            if not found:
                lines.append(f"{key}={new_value}\n")
            with open(self.env_file, "w") as f:
                f.writelines(lines)
        self._cache[key] = new_value
        os.environ[key] = new_value

    def as_dict(self) -> Dict[str, str]:
        # For debugging or export
        d = dict(self._cache)
        d.update({k: v for k, v in os.environ.items() if k in d or k in self._cache})
        return d

# Singleton instance
secrets = SecretsManager()

# CLI
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Unified Secrets Manager CLI")
    parser.add_argument("get", nargs="?", help="Get a secret by key")
    parser.add_argument("--validate", nargs="*", help="Validate required secrets (space separated)")
    parser.add_argument("--rotate", nargs=2, metavar=("KEY", "VALUE"), help="Rotate (update) a secret")
    parser.add_argument("--dump", action="store_true", help="Dump all loaded secrets (for debug)")
    args = parser.parse_args()
    if args.get:
        print(secrets.get(args.get) or "[Not found]")
    if args.validate:
        print(json.dumps(secrets.validate(args.validate), indent=2))
    if args.rotate:
        key, value = args.rotate
        secrets.rotate(key, value)
        print(f"[Rotated] {key}")
    if args.dump:
        print(json.dumps(secrets.as_dict(), indent=2)) 