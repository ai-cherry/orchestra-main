# Pulumi Infrastructure (`infra/`)

This directory contains the Pulumi program that provisions the Vultr server and supporting resources for Orchestra AI.

## Structure

```
infra/
├── main.py                   # Entry point
├── components/               # Reusable Pulumi components
│   ├── vultr_server_component.py  # Single-node server with nightly snapshot
│   └── ...
├── requirements.txt          # Pulumi Python dependencies
├── Pulumi.yaml               # Project configuration
└── Pulumi.*.yaml             # Stack configs
```

## Prerequisites

- Python 3.10
- Pulumi CLI installed
- `VULTR_API_KEY` and `PULUMI_ACCESS_TOKEN` set in the environment

## Quick Start

```bash
pip install -r requirements.txt
pulumi stack init dev
pulumi config set --secret vultr:apiKey $VULTR_API_KEY
pulumi up
```

Pulumi state is stored in Pulumi Cloud; no additional setup is required.

## Component Overview

### `VultrServerComponent`
Provisions:
- Bare-metal instance with attached block storage
- Snapshot cron job via `scripts/snapshot.sh`
- Firewall rules for HTTP/SSH/Postgres

### `database_component.py`
Defines optional DragonflyDB and MongoDB resources if needed.

## Common Commands

```bash
pulumi preview        # Show planned changes
pulumi up             # Deploy infrastructure
pulumi refresh        # Sync state
pulumi destroy        # Tear down
```

## Troubleshooting

1. Verify `VULTR_API_KEY` is correct and not rate limited.
2. Run `pulumi refresh` if resources become out of sync.

For full details see [`docs/RECOVERY.md`](../docs/RECOVERY.md).
