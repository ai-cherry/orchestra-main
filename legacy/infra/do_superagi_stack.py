"""
"""
env = config.require("env")  # "dev" or "prod"
droplet_size = config.get("droplet_size") or ("s-1vcpu-2gb" if env == "dev" else "s-2vcpu-4gb")
region = config.get("region") or "sfo2"  # Ensure this region supports App Platform
hostname = config.get("hostname") or (
    f"superagi-{env}-sfo2-01" if env == "dev" else "ubuntu-s-2vcpu-8gb-160gb-intel-sfo2-01"
)

ssh_pubkey_path = config.get("ssh_pubkey_path")  # Path to local SSH public key file
ssh_private_key_path = config.get_secret("ssh_private_key_path")  # Path to local SSH private key file

# --- SECRETS ---
weaviate_url = config.require_secret("weaviate_url")
weaviate_api_key = config.require_secret("weaviate_api_key")
superagi_image = config.get("superagi_image") or "superagi/superagi:latest"

# --- Admin UI Configuration ---
admin_ui_custom_domain_name = config.get("adminUiCustomDomain")
# Path from infra/do_superagi_stack.py to admin-ui/dist/.
# Assumes `pulumi up` is run from `infra/` directory.
# `os.path.dirname(__file__)` gives the directory of the current script (`infra/`)
# `os.path.join(script_dir, "..", "admin-ui", "dist")` constructs `infra/../admin-ui/dist`
admin_ui_dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "admin-ui", "dist"))

# --- SSH KEY RESOURCE ---
ssh_key_resource = None
if ssh_pubkey_path:
    with open(os.path.expanduser(ssh_pubkey_path), "r") as f:
        ssh_pubkey_content = f.read()
    ssh_key_resource = do.SshKey(f"{env}-ssh-key", name=f"{env}-ssh-key-{env}", public_key=ssh_pubkey_content)

# --- DROPLET ---
cloud_init = f"""
  - docker pull {superagi_image}
"""
    f"superagi-{env}-droplet",
    name=hostname,
    region=region,
    size=droplet_size,
    image="ubuntu-22-04-x64",
    ssh_keys=[ssh_key_resource.fingerprint] if ssh_key_resource else [],
    tags=[f"superagi-{env}"],
    user_data=cloud_init,
)

# --- REMOTE COMMAND: RUN SUPERAGI DOCKER CONTAINER ---
# Determine connection arguments
if ssh_private_key_path:
    # Read the SSH private key
    ssh_private_key_path_str = config.get("ssh_private_key_path")
    if ssh_private_key_path_str:
        with open(os.path.expanduser(ssh_private_key_path_str), "r") as f:
            ssh_private_key_content = f.read()
        connection = command.remote.ConnectionArgs(
            host=droplet.ipv4_address,
            private_key=ssh_private_key_content,
        )
    else:
        raise pulumi.RunError("ssh_private_key_path is configured but empty")
    connection = command.remote.ConnectionArgs(
        host=droplet.ipv4_address,
    )
else:
    # Fallback or error if no auth method provided

run_superagi = command.remote.Command(
    f"run-superagi-{env}",
    connection=connection,
    # Use Output.all to ensure secrets are resolved before forming the command
    create=Output.all(
        weaviate_url=weaviate_url,
        weaviate_api_key=weaviate_api_key,
    ).apply(
        lambda args: f"""
Environment="PYTHONPATH=/opt/cherry_ai"
Environment="WEAVIATE_URL={args['weaviate_url']}"
Environment="WEAVIATE_API_KEY={args['weaviate_api_key']}"
ExecStart=/usr/bin/python3 -m uvicorn core.api.main:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start the service
systemctl daemon-reload
systemctl enable cherry_ai-api
systemctl start cherry_ai-api
"""
        protocol="tcp",
        port_range="8080",  # SuperAGI
        source_addresses=["0.0.0.0/0", "::/0"],
    ),
    do.FirewallInboundRuleArgs(
        protocol="tcp",
        port_range="22",  # SSH
        source_addresses=["0.0.0.0/0", "::/0"],
    ),
]

firewall = do.Firewall(
    f"superagi-{env}-firewall",
    name=f"superagi-{env}-firewall",
    droplet_ids=[droplet.id],
    inbound_rules=firewall_rules_inbound,
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

# --- DigitalOcean App Platform for Admin UI ---
# Check if the admin_ui_dist_path exists. This is a deployment-time check.
# Pulumi needs this path to be valid on the machine running `pulumi up`.
# In CI, this path (`../admin-ui/dist` relative to `infra/`) must contain the build artifact.
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
            error_document="index.html",  # Optional: custom error page
            catchall_document="index.html",  # Optional: for SPAs, route all paths to index.html
        )
    ],
}

if admin_ui_custom_domain_name:
    admin_app_spec_dict["domains"] = [admin_ui_custom_domain_name]

admin_app = do.App(
    f"admin-ui-app-{env}",
    spec=do.AppSpecArgs(**admin_app_spec_dict),
)

# --- OUTPUTS ---
pulumi.export("droplet_ip", droplet.ipv4_address)
pulumi.export("superagi_url", Output.concat("http://", droplet.ipv4_address, ":8080"))
pulumi.export("hostname", droplet.name)
pulumi.export("admin_ui_default_url", admin_app.default_ingress)
pulumi.export("admin_ui_live_url", admin_app.live_url)
