# TODO: Consider adding connection pooling configuration
"""
"""
        self.region = config.get("region") or "nyc3"
        self.cluster_size = config.get("cluster_size") or "db-s-1vcpu-2gb"
        self.node_count = config.get("node_count") or 1
        self.version = config.get("version") or "7"

        self._setup_database()

    def _setup_database(self):
            version=self.version,
            size=self.cluster_size,
            region=self.region,
            node_count=self.node_count,
            project_id=self.config.require("project_id"),
            tags=["cherry_ai", "database"],
        )

        # Create database user
        self.db_user = do.DatabaseUser(
            f"{self._name}-db-user",
            cluster_id=self.cluster.id,
            mysql_auth_plugin="caching_sha2_password",
        )

        # Create firewall rules
        self.firewall = do.DatabaseFirewall(
            f"{self._name}-db-firewall",
            cluster_id=self.cluster.id,
            rules=[{"type": "ip_addr", "value": "0.0.0.0/0"}],  # Restrict in production
        )

        # Export connection details
        pulumi.export(
            Output.concat(
                self.db_user.name,
                ":",
                self.db_user.password,
                "@",
                self.cluster.private_host,
                "/admin?retryWrites=true&w=majority",
            ),
        )
