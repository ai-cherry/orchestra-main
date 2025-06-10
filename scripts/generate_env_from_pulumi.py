#!/usr/bin/env python3
"""Generate a local .env from Pulumi configuration."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Any


def get_pulumi_config() -> Dict[str, Any]:
    """Return Pulumi config including secrets."""
    infra_dir = Path(__file__).resolve().parent.parent / "infra"
    original_dir = Path.cwd()
    os.chdir(infra_dir)
    try:
        passphrase = os.getenv("PULUMI_CONFIG_PASSPHRASE", "")
        if passphrase:
            os.environ["PULUMI_CONFIG_PASSPHRASE"] = passphrase
        result = subprocess.run(
            ["pulumi", "config", "--show-secrets", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    finally:
        os.chdir(original_dir)


def generate_env_file(config: Dict[str, Any], output_path: Path) -> None:
    """Write environment variables to the given path."""
    env_lines = []
    for key, data in config.items():
        env_key = key.upper().replace(":", "_")
        env_lines.append(f"{env_key}={data['value']}")

    env_lines.extend(
        [
            "SITE_URL=http://localhost:8000",
            "SITE_TITLE=Cherry AI Development",
            "API_HOST=0.0.0.0",
            "API_PORT=8000",
        ]
    )

    output_path.write_text("\n".join(env_lines) + "\n")
    print(f"✅ Generated {output_path}")

    example_lines = [
        line.split("=")[0] + "=your_value_here" if any(x in line for x in ["KEY", "TOKEN", "PASSWORD", "SECRET"]) else line
        for line in env_lines
    ]
    example_path = output_path.parent / ".env.example"
    example_path.write_text("\n".join(example_lines) + "\n")
    print(f"✅ Generated {example_path}")


def main() -> int:
    print("📥 Reading Pulumi configuration...")
    try:
        config = get_pulumi_config()
        env_path = Path(__file__).resolve().parent.parent / ".env"
        generate_env_file(config, env_path)
        print("\n🎉 Environment setup complete!")
        print("   Run: source .env")
        return 0
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"❌ Error generating .env: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
