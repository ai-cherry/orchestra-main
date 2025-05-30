# Pulumi Infrastructure (`infra/`)

This directory contains the Pulumi code for provisioning the single-node Vultr environment that runs the Orchestra platform.

## Structure
```text
infra/
├── main.py                  # Entry point for Pulumi
├── components/              # Reusable Pulumi components
│   └── vultr_server_component.py  # Bare-metal server + volume + snapshot cron
├── requirements.txt         # Python dependencies for Pulumi
├── Pulumi.yaml              # Project configuration
└── Pulumi.<stack>.yaml      # Stack configs (dev, prod)
```

## Prerequisites
- Python 3.10
- Pulumi CLI installed
- `VULTR_API_KEY` and `PULUMI_ACCESS_TOKEN` set as environment variables

## Quick Start
```bash
pip install -r requirements.txt
pulumi stack init dev   # once
pulumi config set vultr:apiKey $VULTR_API_KEY --secret
pulumi up
```

## Snapshot Automation
`vultr_server_component.py` installs `/root/snapshot.sh` and schedules it via cron at 03:00 UTC. The script calls `vultr-cli snapshot create` for the attached volume so nightly backups are automatic.

## Common Commands
```bash
pulumi preview     # Show proposed changes
pulumi up          # Apply changes
pulumi destroy     # Tear down the stack
```

The only stack output is the public IP of the server. All secrets are stored in Pulumi config or GitHub Secrets.
