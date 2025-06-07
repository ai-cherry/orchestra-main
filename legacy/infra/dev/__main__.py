from __future__ import annotations

"""Pulumi dev stack – provisions a single Lambda Labs VPS for development.

Usage:
    # Set stack and config first time
    pulumi stack init dev
    pulumi config set dev:sshKeyIds "123,456"
    pulumi config set dev:sshPrivateKey --secret "$(cat ~/.ssh/id_rsa)"

    # Deploy
    pulumi up

Outputs:
    ipAddress:  Public IPv4 of the instance (SSH / HTTP entrypoint).
"""

from typing import List, Optional, TypedDict

import pulumi
import pulumi_lambdalabs as ldl
from pulumi import Config, Output
from pulumi_command import remote


class DevServerArgs(TypedDict):
    plan: str
    region: str
    volume_size_gb: int
    ssh_key_ids: Optional[List[str]]
    ssh_private_key: Optional[str]


cfg = Config()
args: DevServerArgs = {
    "plan": cfg.get("dev:plan") or "gpu_1x_a10",
    "region": cfg.get("dev:region") or "us-west-1",
    "volume_size_gb": int(cfg.get("dev:volumeSizeGb") or 100),
    "ssh_key_ids": (
        cfg.get("dev:sshKeyIds").split(",") if cfg.get("dev:sshKeyIds") else None
    ),
    "ssh_private_key": cfg.get_secret("dev:sshPrivateKey"),
}

# 1. Provision the instance -------------------------------------------------------------------
server = ldl.Instance(
    "orchestra-dev-instance",
    plan=args["plan"],
    region=args["region"],
    os_id=215,  # Ubuntu 22.04 LTS
    ssh_key_ids=args["ssh_key_ids"],
)

# 2. Optional block storage -------------------------------------------------------------------
volume = ldl.BlockStorage(
    "orchestra-dev-volume",
    region=server.region,
    size_gb=args["volume_size_gb"],
)

_ = ldl.VolumeAttachment(
    "orchestra-dev-volume-attach",
    instance_id=server.id,
    volume_id=volume.id,
)

# 3. Basic bootstrap (update & install build essentials) --------------------------------------
if args["ssh_private_key"] is not None and args["ssh_key_ids"] is not None:
    conn = remote.ConnectionArgs(
        host=server.ip_address,
        user="ubuntu",
        private_key=args["ssh_private_key"],
    )

    remote.Command(
        "orchestra-dev-bootstrap",
        connection=conn,
        create="""
            sudo apt-get update -y && sudo apt-get install -y git tmux htop build-essential
            # Prevent interactive tzdata prompt
            sudo DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata
        """,
    )

# 4. Export outputs ---------------------------------------------------------------------------
pulumi.export("ipAddress", server.ip_address) 