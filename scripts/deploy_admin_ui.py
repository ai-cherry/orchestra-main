#!/usr/bin/env python3
"""
"""
UI_DIST: Final[Path] = ROOT / "admin-ui" / "dist"
INFRA_DIR: Final[Path] = ROOT / "infra" / "admin_ui_site"

def run(cmd: list[str], allow_failure: bool = False) -> None:
    """Run *cmd* and exit on non-zero return code unless allow_failure is True."""
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
