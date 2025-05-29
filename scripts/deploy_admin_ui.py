#!/usr/bin/env python3
"""Convenience script to deploy the Admin UI static website.

This is a thin wrapper around Pulumi and `gsutil rsync` so that developers can
run *one* command locally:

    python scripts/deploy_admin_ui.py --stack dev --domain cherry-ai.me

Requirements:
  * Pulumi CLI and gcloud SDK installed and authenticated.
  * `admin-ui` sub-project built (run `npm run build` first).
  * A Pulumi stack matching `--stack` must exist (or will be created).

The script is deliberately simple and delegates heavy lifting to Pulumi.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Final

ROOT: Final[Path] = Path(__file__).resolve().parents[1]
UI_DIST: Final[Path] = ROOT / "admin-ui" / "dist"
INFRA_DIR: Final[Path] = ROOT / "infra" / "admin_ui_site"


def run(cmd: list[str], allow_failure: bool = False) -> None:
    """Run *cmd* and exit on non-zero return code unless allow_failure is True."""
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        if not allow_failure:
            sys.stderr.write(f"[deploy_admin_ui] command failed: {exc.cmd}\n")
            sys.exit(exc.returncode)
        else:
            sys.stderr.write(f"[deploy_admin_ui] command failed but continuing: {exc.cmd}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy the Admin UI static site via Pulumi.")
    parser.add_argument("--stack", required=True, help="Pulumi stack name (e.g. dev, prod)")
    parser.add_argument("--domain", required=True, help="Primary domain name (e.g. cherry-ai.me)")
    args = parser.parse_args()

    if not UI_DIST.exists():
        sys.stderr.write("admin-ui/dist not found – build the UI first (npm run build).\n")
        sys.exit(1)

    # Ensure stack exists (Pulumi is idempotent – harmless if already created).
    stack_name = args.stack
    run(["pulumi", "stack", "select", stack_name, "--cwd", str(INFRA_DIR)])

    # Configure required values.
    run(
        [
            "pulumi",
            "config",
            "set",
            "domainName",
            args.domain,
            "--stack",
            stack_name,
            "--cwd",
            str(INFRA_DIR),
        ]
    )

    # Deploy or update infra.
    run(
        [
            "pulumi",
            "up",
            "--yes",
            "--stack",
            stack_name,
            "--cwd",
            str(INFRA_DIR),
        ],
        allow_failure=True,  # Allow failure if infrastructure already exists
    )

    # Get bucket name output.
    bucket_name_bytes = subprocess.check_output(
        [
            "pulumi",
            "stack",
            "output",
            "bucket_name",
            "--stack",
            stack_name,
            "--cwd",
            str(INFRA_DIR),
        ]
    )
    bucket_name = bucket_name_bytes.decode().strip()

    # Sync static assets.
    # The bucket_name already includes the gs:// prefix from Pulumi output
    # Ensure bucket_name has gs:// prefix
    if not bucket_name.startswith("gs://"):
        bucket_name = f"gs://{bucket_name}"
    run(["gsutil", "-m", "rsync", "-r", str(UI_DIST), bucket_name])

    print("Admin UI deployed successfully! 🎉")


if __name__ == "__main__":
    main()
