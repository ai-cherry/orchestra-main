import pulumi
import pulumi_vultr as vultr
import pulumi_command as command
from pulumi import ComponentResource, ResourceOptions


class VultrServerComponent(ComponentResource):
    """Single-node Vultr server for Orchestra AI."""

    def __init__(self, name: str, config: dict, opts: ResourceOptions | None = None):
        super().__init__("orchestra:vultr:ServerComponent", name, None, opts)
        self.config = config

        self.server = vultr.Instance(
            f"{name}-instance",
            plan=config.get("plan", "vhp-16c-64gb"),
            region=config.get("region", "ewr"),
            os_id=config.get("os_id", 215),  # Ubuntu 24.04 x64
            ssh_key_ids=config.get("ssh_key_ids"),
        )

        self.volume = vultr.BlockStorage(
            f"{name}-volume",
            region=self.server.region,
            size_gb=config.get("volume_size_gb", 500),
        )

        self.attach = vultr.VolumeAttachment(
            f"{name}-vol-attach",
            instance_id=self.server.id,
            volume_id=self.volume.id,
        )

        conn = command.remote.ConnectionArgs(
            host=self.server.main_ip,
            user="root",
            private_key=config.get("ssh_private_key"),
        )

        self.setup = command.remote.Command(
            f"{name}-setup",
            connection=conn,
            create="""
                apt-get update && apt-get install -y docker.io docker-compose curl
                mkdir -p /data
                mount {device} /data || true
            """,
        )

        # Nightly snapshot cron job
        self.snapshot_cron = command.remote.Command(
            f"{name}-snapshot-cron",
            connection=conn,
            create="""
                cat > /root/snapshot.sh <<'EOF'
#!/bin/bash
set -e
VOLUME_ID="{volume_id}"
SNAP_ID=$(vultr-cli snapshot create "$VOLUME_ID" | awk '{print $NF}')
echo "Snapshot $SNAP_ID created" >> /var/log/vultr-snapshot.log
EOF
                chmod +x /root/snapshot.sh
                (crontab -l 2>/dev/null || echo "") | grep -v 'snapshot.sh' | { cat; echo '0 3 * * * /root/snapshot.sh'; } | crontab -
            """.format(volume_id=self.volume.id),
            opts=ResourceOptions(parent=self.attach),
        )

        self.register_outputs({"ip": self.server.main_ip, "volume_id": self.volume.id})
