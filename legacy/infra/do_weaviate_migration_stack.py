import os
# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
env = config.require("env")  # "dev" or "prod"

# Existing droplet IDs - these should be your actual droplet IDs
vector_droplet_id = config.require("vector_droplet_id")  # superagi-dev-sfo2-01
app_droplet_id = config.require("app_droplet_id")  # ubuntu-s-2vcpu-8gb-160gb-intel-sfo2-01

# Region and network
region = config.get("region") or "sfo2"
vpc_cidr = config.get("vpc_cidr") or "10.120.0.0/16"

# Droplet sizes for potential resize operations
vector_droplet_size = config.get("vector_droplet_size") or "c-4"  # CPU-optimized, 4 vCPU / 8 GB
app_droplet_size = config.get("app_droplet_size") or "g-8vcpu-32gb"  # General-purpose, 8 vCPU / 32 GB

# Weaviate configuration
weaviate_version = config.get("weaviate_version") or "1.30.1"
weaviate_volume_size_gb = config.get_int("weaviate_volume_size_gb") or 160
weaviate_api_key = config.require_secret("weaviate_api_key")
enable_acorn = config.get_bool("enable_acorn") or True
enable_agents = config.get_bool("enable_agents") or True

# PostgreSQL configuration
postgres_version = config.get("postgres_version") or "16"
postgres_db_name = config.get("postgres_db_name") or "conductor"
postgres_user = config.get("postgres_user") or "conductor"
postgres_password = config.require_secret("postgres_password")

# SSH authentication
ssh_private_key = config.require_secret("ssh_private_key")

enable_micro_cache = config.get_bool("enable_micro_cache") or False
micro_cache_droplet_size = config.get("micro_cache_droplet_size") or "s-1vcpu-1gb"

# Admin UI Configuration
admin_ui_custom_domain_name = config.get("adminUiCustomDomain")
admin_ui_dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "admin-ui", "dist"))

# --- FETCH EXISTING DROPLETS ---
vector_droplet = do.get_droplet(id=vector_droplet_id)
app_droplet = do.get_droplet(id=app_droplet_id)

# --- VECTOR DROPLET COMPONENT (WEAVIATE) ---
vector_node = VectorDropletComponent(
    name=f"vector-node-{env}",
    config={
        "droplet_id": vector_droplet_id,
        "droplet_name": vector_droplet.name,
        "region": region,
        "volume_size_gb": weaviate_volume_size_gb,
        "weaviate_version": weaviate_version,
        "enable_acorn": enable_acorn,
        "enable_agents": enable_agents,
        "ssh_private_key": ssh_private_key,
    },
    opts=ResourceOptions(
        protect=True,  # Protect the existing droplet from deletion
    ),
)

# --- APP DROPLET COMPONENT (POSTGRES + CONDUCTOR) ---
app_node = PostgresComponent(
    name=f"app-node-{env}",
    config={
        "droplet_id": app_droplet_id,
        "droplet_name": app_droplet.name,
        "db_name": postgres_db_name,
        "db_user": postgres_user,
        "db_password": postgres_password,
        "ssh_private_key": ssh_private_key,
        "allowed_hosts": [vpc_cidr],
        "python_packages": [
            "superagi",
            "autogen",
            "weaviate-client",
            "psycopg2-binary",
            "langfuse",
            "sentence-transformers",
            "uvicorn",
            "fastapi",
        ],
    },
    opts=ResourceOptions(
        protect=True,  # Protect the existing droplet from deletion
    ),
)

micro_cache_droplet = None
if enable_micro_cache:
    micro_cache_droplet = do.Droplet(
        f"micro-cache-{env}",
        name=f"micro-cache-{env}",
        region=region,
        size=micro_cache_droplet_size,
        image="docker-20-04",
        tags=[f"cherry_ai-{env}", "micro-cache"],
    )

    # Setup connection for remote commands
    micro_cache_connection = command.remote.ConnectionArgs(
        host=micro_cache_droplet.ipv4_address,
        user="root",
        private_key=ssh_private_key,
    )

        connection=micro_cache_connection,
        create="""
EOF


            # Add to crontab
        """
        f"micro-cache-firewall-{env}",
        droplet_ids=[micro_cache_droplet.id],
        inbound_rules=[
            do.FirewallInboundRuleArgs(
                protocol="tcp",
                port_range="22",
                source_addresses=["0.0.0.0/0", "::/0"],
            ),
            do.FirewallInboundRuleArgs(
                protocol="tcp",
                source_addresses=[vpc_cidr],
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
    )

# --- ADMIN UI DEPLOYMENT ---
# Check if the admin_ui_dist_path exists
if not os.path.isdir(admin_ui_dist_path):
    pulumi.log.warn(
        f"Admin UI source directory {admin_ui_dist_path} does not exist or is not a directory. App Platform deployment might fail or deploy an empty site."
    )

admin_app_spec_dict = {
    "name": f"admin-ui-{env}",
    "region": region,
    "static_sites": [
        do.AppSpecStaticSiteArgs(
            name="admin-ui-site",
            build_command=None,  # No build command needed as we provide pre-built static assets
            source_dir=admin_ui_dist_path,  # Path to the directory containing static files
            index_document="index.html",
            error_document="index.html",  # For SPAs, route all paths to index.html
            catchall_document="index.html",  # For SPAs, route all paths to index.html
            env_vars=[
                do.AppSpecStaticSiteEnvVarArgs(
key = os.getenv("ORCHESTRA_DO_WEAVIATE_MIGRATION_STACK_KEY", "")
                    value=Output.concat("http://", app_droplet.ipv4_address, ":8080"),
                ),
                do.AppSpecStaticSiteEnvVarArgs(
key = os.getenv("ORCHESTRA_DO_WEAVIATE_MIGRATION_STACK_KEY", "")
                    value=Output.concat("http://", vector_droplet.ipv4_address, ":8080"),
                ),
            ],
        )
    ],
}

if admin_ui_custom_domain_name:
    admin_app_spec_dict["domains"] = [admin_ui_custom_domain_name]

admin_app = do.App(
    f"admin-ui-app-{env}",
    spec=do.AppSpecArgs(**admin_app_spec_dict),
)

# --- SETUP cherry_ai API SERVICE ---
setup_cherry_ai_service = command.remote.Command(
    f"setup-cherry_ai-service-{env}",
    connection=command.remote.ConnectionArgs(
        host=app_droplet.ipv4_address,
        user="root",
        private_key=ssh_private_key,
    ),
    create=Output.all(
        weaviate_endpoint=vector_node.weaviate_endpoint,
        weaviate_api_key=weaviate_api_key,
        postgres_dsn=app_node.postgres_dsn,
        micro_cache_uri=micro_cache_droplet.ipv4_address if enable_micro_cache else None,
    ).apply(
        lambda args: f"""
Environment="PYTHONPATH=/opt/cherry_ai"
EnvironmentFile=/opt/cherry_ai/.env
ExecStart=/opt/cherry_ai/venv/bin/python -m uvicorn core.api.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and restart service
systemctl daemon-reload
systemctl enable cherry_ai-api
systemctl restart cherry_ai-api

# Setup migration scripts
mkdir -p /opt/cherry_ai/migrations
cat > /opt/cherry_ai/migrations/run_migration.sh << 'EOF'
#!/bin/bash
cd /opt/cherry_ai
source venv/bin/activate
python scripts/setup_weaviate_collections.py
EOF

chmod +x /opt/cherry_ai/migrations/run_migration.sh
"""
    f"setup-latency-monitoring-{env}",
    connection=command.remote.ConnectionArgs(
        host=app_droplet.ipv4_address,
        user="root",
        private_key=ssh_private_key,
    ),
    create=Output.all(
        weaviate_endpoint=vector_node.weaviate_endpoint,
    ).apply(
        lambda args: f"""
WEAVIATE_ENDPOINT = "{args['weaviate_endpoint']}"
WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY", "")
RESULTS_FILE = "/var/log/weaviate_latency.json"
SAMPLE_SIZE = 10
THRESHOLD_MS = 50  # 50ms threshold for considering micro-cache

def measure_weaviate_latency():
    headers = {{}}
    if WEAVIATE_API_KEY:
        headers["Authorization"] = "Bearer " + WEAVIATE_API_KEY

    latencies = []
    for _ in range(SAMPLE_SIZE):
        try:

            pass
            start = time.time()
            response = requests.get(WEAVIATE_ENDPOINT + "/v1/.well-known/ready", headers=headers, timeout=30)
            end = time.time()

            if response.status_code == 200:
                latency_ms = (end - start) * 1000  # Convert to milliseconds
                latencies.append(latency_ms)
            else:
                print("Error: Received status code " + str(response.status_code))
        except Exception:

            pass
            print("Request failed: " + str(e))

        # Small delay between requests
        # TODO: Replace with asyncio.sleep() for async code
        time.sleep(0.5)

    if not latencies:
        return None

    # Calculate statistics
    avg_latency = statistics.mean(latencies)
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
    min_latency = min(latencies)
    max_latency = max(latencies)

    result = {{
        "timestamp": datetime.datetime.now().isoformat(),
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
        "min_latency_ms": min_latency,
        "max_latency_ms": max_latency,
        "sample_size": len(latencies),
        "needs_micro_cache": p95_latency > THRESHOLD_MS
    }}

    # Save results
    try:

        pass
        existing_data = []
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, 'r') as f:
                existing_data = json.load(f)

        # Keep only the last 100 measurements
        existing_data.append(result)
        if len(existing_data) > 100:
            existing_data = existing_data[-100:]

        with open(RESULTS_FILE, 'w') as f:
            json.dump(existing_data, f, indent=2)
    except Exception:

        pass
        print("Failed to save results: " + str(e))

    return result

if __name__ == "__main__":
    result = measure_weaviate_latency()
    if result:
        print(json.dumps(result, indent=2))
        if result["needs_micro_cache"]:
            print("WARNING: p95 latency exceeds threshold. Consider enabling micro-cache.")
EOF

chmod +x /opt/cherry_ai/monitor_latency.py

# Create cron job to run every hour
# Fixed the f-string syntax error by escaping the nested quotes
echo \"0 * * * * /opt/cherry_ai/venv/bin/python /opt/cherry_ai/monitor_latency.py >> /var/log/latency_monitor.log 2>&1\" | crontab -
"""
pulumi.export("vector_node_ip", vector_droplet.ipv4_address)
pulumi.export("app_node_ip", app_droplet.ipv4_address)
pulumi.export("weaviate_endpoint", vector_node.weaviate_endpoint)
pulumi.export("postgres_dsn", app_node.postgres_dsn)
pulumi.export("admin_ui_default_url", admin_app.default_ingress)
pulumi.export("admin_ui_live_url", admin_app.live_url)
if enable_micro_cache and micro_cache_droplet:
    pulumi.export("micro_cache_ip", micro_cache_droplet.ipv4_address)
pulumi.export("cherry_ai_api_url", Output.concat("http://", app_droplet.ipv4_address, ":8080"))
