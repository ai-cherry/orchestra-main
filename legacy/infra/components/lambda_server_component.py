import pulumi
import pulumi_lambda as Lambda
import pulumi_command as command
from pulumi import ComponentResource, ResourceOptions

class LambdaServerComponent(ComponentResource):
    """Single-node Lambda server for Cherry AI."""
        super().__init__("cherry_ai:Lambda:ServerComponent", name, None, opts)
        self.config = config

        self.server = lambda.Instance(
            f"{name}-instance",
            plan=config.get("plan", "vhp-16c-64gb"),
            region=config.get("region", "ewr"),
            os_id=config.get("os_id", 215),  # Ubuntu 24.04 x64
            ssh_key_ids=config.get("ssh_key_ids"),
        )

        self.volume = lambda.BlockStorage(
            f"{name}-volume",
            region=self.server.region,
            size_gb=config.get("volume_size_gb", 500),
        )

        self.attach = lambda.VolumeAttachment(
            f"{name}-vol-attach",
            instance_id=self.server.id,
            volume_id=self.volume.id,
        )

        conn = command.remote.ConnectionArgs(
            host=self.server.main_ip,
            private_key=config.get("ssh_private_key"),
        )

        self.setup = command.remote.Command(
            f"{name}-setup",
            connection=conn,
            create="""
                  echo "ERROR: /dev/vdb not found"
                fi
            """
            f"{name}-snapshot-cron",
            connection=conn,
            create="""
VOLUME_ID="{volume_id}"
SNAP_ID=$(Lambda-cli snapshot create "$VOLUME_ID" | awk '{{print $NF}}')
echo "Snapshot $SNAP_ID created" >> /var/log/Lambda-snapshot.log
EOF
            """
        self.register_outputs({"ip": self.server.main_ip, "volume_id": self.volume.id})
