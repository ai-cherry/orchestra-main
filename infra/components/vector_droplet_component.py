# TODO: Consider adding connection pooling configuration
"""
        name="vector-node",
        config={
            "droplet_id": "existing-droplet-id",  # ID of existing droplet
            "droplet_name": "superagi-dev-sfo2-01",  # Name for reference
            "region": "sfo2",  # Must match droplet region
            "volume_size_gb": 160,
            "weaviate_version": "1.30.1",
            "enable_acorn": True,
            "enable_agents": True,
            "ssh_private_key": "...",  # Pulumi config key
        },
        opts=ResourceOptions(...)
    )
"""
    """
    """
        super().__init__("orchestra:vector:DropletComponent", name, None, opts)

        self.config = config
        self.droplet_id = config.get("droplet_id")
        self.droplet_name = config.get("droplet_name", "vector-node")
        self.region = config.get("region", "sfo2")
        self.volume_size_gb = config.get("volume_size_gb", 160)
        self.weaviate_version = config.get("weaviate_version", "1.30.1")
        self.enable_acorn = config.get("enable_acorn", True)
        self.enable_agents = config.get("enable_agents", True)
        self.ssh_private_key = config.get("ssh_private_key")

        # Get existing droplet by ID
        self.droplet = do.get_droplet(id=self.droplet_id)

        # Create block storage volume if not exists
        volume_name = f"{self.droplet_name}-vector-data"
        self.volume = do.Volume(
            f"{name}-volume",
            name=volume_name,
            region=self.region,
            size=self.volume_size_gb,
            initial_filesystem_type="ext4",
            description=f"Vector database storage for {self.droplet_name}",
            opts=ResourceOptions(parent=self),
        )

        # Attach volume to droplet
        self.volume_attachment = do.VolumeAttachment(
            f"{name}-volume-attachment",
            droplet_id=self.droplet_id,
            volume_id=self.volume.id,
            opts=ResourceOptions(parent=self),
        )

        # Setup connection for remote commands
        connection = command.remote.ConnectionArgs(
            host=self.droplet.ipv4_address,
            user="root",
            private_key=self.ssh_private_key,
        )

        # Install Docker and dependencies
        self.setup_docker = command.remote.Command(
            f"{name}-setup-docker",
            connection=connection,
            create="""
            """
            f"{name}-mount-volume",
            connection=connection,
            create=Output.concat(
                "device=$(lsblk -o NAME,SERIAL -J | jq -r '.blockdevices[] | select(.serial == \"",
                self.volume.id,
                '") | "/dev/" + .name\')\n',
                """
                echo "Mounting $device to /mnt/vector-data"
                
                # Check if already mounted
                if grep -qs '/mnt/vector-data' /proc/mounts; then
                    echo "Volume already mounted"
                else
                    # Format if needed
                    if ! blkid $device; then
                        mkfs.ext4 $device
                    fi
                    
                    # Mount
                    mount $device /mnt/vector-data
                    
                    # Add to fstab for persistence
                    if ! grep -qs "$device" /etc/fstab; then
                        echo "$device /mnt/vector-data ext4 defaults,nofail 0 2" >> /etc/fstab
                    fi
                fi
                
                # Set permissions
                chown -R root:root /mnt/vector-data
                chmod -R 755 /mnt/vector-data
                """
        modules = "text2vec-openai,reranker-openai"
        if self.enable_agents:
            modules += ",agents"

        env_vars = [
            "CLUSTER_HOSTNAME=node1",
            "PERSISTENCE_DATA_PATH=/var/lib/weaviate",
            "DEFAULT_VECTORIZER_MODULE=text2vec-openai",
            f"ENABLE_MODULES={modules}",
            "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=false",
            "AUTHENTICATION_APIKEY_ENABLED=true",
            "AUTHENTICATION_APIKEY_ALLOWED_KEYS=readonlykey,adminkey,importkey",
            "AUTHENTICATION_APIKEY_USERS=readonlyuser,adminuser,importuser",
            "AUTHENTICATION_APIKEY_ROLES=readonly,admin,import",
            "CLUSTER_DATA_REPLICATION_FACTOR=1",
        ]

        if self.enable_acorn:
            env_vars.append("QUERY_DEFAULT_ACORN_ENABLED=true")

        env_vars_str = "\n      - ".join(env_vars)

        self.deploy_weaviate = command.remote.Command(
            f"{name}-deploy-weaviate",
            connection=connection,
            create=Output.concat(
                f"""
      - "8080:8080"
      - "50051:50051"
    volumes:
      - /mnt/vector-data:/var/lib/weaviate
    environment:
      - """
                """
      test: ["CMD", "curl", "-f", "http://localhost:8080/v1/.well-known/ready"]
      interval: 10s
      timeout: 5s
      retries: 5
EOF

                # Start Weaviate
                cd /root
                docker-compose -f weaviate-compose.yml up -d

                # Wait for Weaviate to be ready
                echo "Waiting for Weaviate to be ready..."
                timeout 300 bash -c 'until curl -s -f http://localhost:8080/v1/.well-known/ready; do sleep 5; done'
                echo "Weaviate is ready!"
                """
            f"{name}-firewall",
            droplet_ids=[self.droplet_id],
            inbound_rules=[
                do.FirewallInboundRuleArgs(
                    protocol="tcp",
                    port_range="22",
                    source_addresses=["0.0.0.0/0", "::/0"],
                ),
                do.FirewallInboundRuleArgs(
                    protocol="tcp",
                    port_range="8080",  # Weaviate REST API
                    source_addresses=["0.0.0.0/0", "::/0"],
                ),
                do.FirewallInboundRuleArgs(
                    protocol="tcp",
                    port_range="50051",  # Weaviate gRPC
                    source_addresses=["0.0.0.0/0", "::/0"],
                ),
            ],
            outbound_rules=[
                do.FirewallOutboundRuleArgs(
                    protocol="tcp",
                    port_range="all",
                    destination_addresses=["0.0.0.0/0", "::/0"],
                ),
                do.FirewallOutboundRuleArgs(
                    protocol="udp",
                    port_range="all",
                    destination_addresses=["0.0.0.0/0", "::/0"],
                ),
            ],
            opts=ResourceOptions(parent=self),
        )

        # Setup nightly snapshots
        self.snapshot_cron = command.remote.Command(
            f"{name}-snapshot-cron",
            connection=connection,
            create="""
SNAPSHOT_DIR="/mnt/vector-data-snapshots"
mkdir -p $SNAPSHOT_DIR

# Create timestamped snapshot
TIMESTAMP=$(date +%Y%m%d%H%M%S)
tar -czf "$SNAPSHOT_DIR/weaviate-$TIMESTAMP.tar.gz" -C /mnt/vector-data .

# Restart Weaviate
docker-compose -f weaviate-compose.yml start weaviate

# Cleanup old snapshots (keep last 7)
find $SNAPSHOT_DIR -name "weaviate-*.tar.gz" -type f -mtime +7 -delete
EOF

                # Make script executable
                chmod +x /root/snapshot-weaviate.sh

                # Add to crontab
                (crontab -l 2>/dev/null || echo "") | grep -v "snapshot-weaviate.sh" | { cat; echo "0 3 * * * /root/snapshot-weaviate.sh > /var/log/weaviate-snapshot.log 2>&1"; } | crontab -
            """
                "droplet_id": self.droplet_id,
                "droplet_name": self.droplet_name,
                "weaviate_endpoint": Output.concat("http://", self.droplet.ipv4_address, ":8080"),
                "weaviate_grpc_endpoint": Output.concat(self.droplet.ipv4_address, ":50051"),
                "volume_id": self.volume.id,
                "volume_size_gb": self.volume_size_gb,
            }
        )
