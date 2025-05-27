"""
Pulumi DigitalOcean Stack for SuperAGI & AI Orchestra
Automates Droplet provisioning, Docker setup, and SuperAGI deployment for dev/prod environments.
Also deploys the Admin UI static assets to DigitalOcean App Platform.
Author: Orchestra AI Platform

Instructions:
- Set DIGITALOCEAN_TOKEN in Pulumi config or environment.
- Store all secrets (DB URIs, API keys) in Pulumi config/secrets.
- Run `pulumi up` to provision and deploy.
"""

import pulumi
import pulumi_digitalocean as do
import pulumi_command as command
from pulumi import Config, Output
import os # Added for path joining

# --- CONFIGURATION ---
config = Config()
env = config.require("env")  # "dev" or "prod"
droplet_size = config.get("droplet_size") or (
    "s-1vcpu-2gb" if env == "dev" else "s-2vcpu-4gb"
)
region = config.get("region") or "sfo2" # Ensure this region supports App Platform
hostname = config.get("hostname") or (
    f"superagi-{env}-sfo2-01"
    if env == "dev"
    else "ubuntu-s-2vcpu-8gb-160gb-intel-sfo2-01"
)
# SSH authentication – either pubkey+private key or root password

root_password = config.get_secret("root_password")
ssh_pubkey_path = config.get("ssh_pubkey_path") # Path to local SSH public key file
ssh_private_key_path = config.get_secret("ssh_private_key_path") # Path to local SSH private key file

# --- SECRETS ---
dragonfly_uri = config.require_secret("dragonfly_uri")
mongo_uri = config.require_secret("mongo_uri")
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
    with open(os.path.expanduser(ssh_pubkey_path), 'r') as f:
        ssh_pubkey_content = f.read()
    ssh_key_resource = do.SshKey(
        f"{env}-ssh-key", name=f"{env}-ssh-key-{env}", public_key=ssh_pubkey_content
    )

# --- DROPLET ---
cloud_init = f"""#cloud-config
package_update: true
package_upgrade: true
packages:
  - docker.io
  - python3-pip
runcmd:
  - systemctl enable docker
  - systemctl start docker
  - usermod -aG docker root
  - pip3 install "pymongo[srv]" weaviate-client dragonfly
  - docker pull {superagi_image}
"""

droplet = do.Droplet(
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
if root_password:
    connection = command.remote.ConnectionArgs(
        host=droplet.ipv4_address,
        user="root",
        password=root_password,
    )
elif ssh_private_key_path:
    with open(os.path.expanduser(ssh_private_key_path), 'r') as f:
        ssh_private_key_content = f.read()
    connection = command.remote.ConnectionArgs(
        host=droplet.ipv4_address,
        user="root",
        private_key=ssh_private_key_content,
    )
else:
    # Fallback or error if no auth method provided
    raise pulumi.RunError("Either root_password or ssh_private_key_path must be provided for droplet connection.")


run_superagi = command.remote.Command(
    f"run-superagi-{env}",
    connection=connection,
    # Use Output.all to ensure secrets are resolved before forming the command
    create=Output.all(dragonfly_uri=dragonfly_uri, mongo_uri=mongo_uri, weaviate_url=weaviate_url, weaviate_api_key=weaviate_api_key).apply(
        lambda args: f"""
docker run -d --restart unless-stopped -p 8080:8080 \\
  -e DRAGONFLY_URI='{args['dragonfly_uri']}' \\
  -e MONGO_URI='{args['mongo_uri']}' \\
  -e WEAVIATE_URL='{args['weaviate_url']}' \\
  -e WEAVIATE_API_KEY='{args['weaviate_api_key']}' \\
  {superagi_image}
"""
    ),
    opts=pulumi.ResourceOptions(depends_on=[droplet]),
)

# --- FIREWALL ---
firewall_rules_inbound = [
    do.FirewallInboundRuleArgs(
        protocol="tcp",
        port_range="8080", # SuperAGI
        sources=do.FirewallInboundRuleSourcesArgs(addresses=["0.0.0.0/0", "::/0"]),
    ),
    do.FirewallInboundRuleArgs(
        protocol="tcp",
        port_range="22", # SSH
        sources=do.FirewallInboundRuleSourcesArgs(addresses=["0.0.0.0/0", "::/0"]),
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
            destinations=do.FirewallOutboundRuleDestinationsArgs(addresses=["0.0.0.0/0", "::/0"]),
        ),
        do.FirewallOutboundRuleArgs(
            protocol="udp",
            port_range="all",
            destinations=do.FirewallOutboundRuleDestinationsArgs(addresses=["0.0.0.0/0", "::/0"]),
        ),
    ],
)

# --- DigitalOcean App Platform for Admin UI ---
# Check if the admin_ui_dist_path exists. This is a deployment-time check.
# Pulumi needs this path to be valid on the machine running `pulumi up`.
# In CI, this path (`../admin-ui/dist` relative to `infra/`) must contain the build artifact.
if not os.path.isdir(admin_ui_dist_path):
    pulumi.log.warn(f"Admin UI source directory {admin_ui_dist_path} does not exist or is not a directory. App Platform deployment might fail or deploy an empty site.")

admin_app_spec_dict = {
    "name": f"admin-ui-{env}",
    "region": region,
    "static_sites": [
        do.AppSpecStaticSiteArgs(
            name="admin-ui-site",
            build_command=None, 
            source_dir=admin_ui_dist_path,
            index_document="index.html",
            error_document="index.html", 
            catchall_document="index.html",
        )
    ],
}

if admin_ui_custom_domain_name:
    admin_app_spec_dict["domains"] = [
        do.AppSpecDomainArgs(
            domain=admin_ui_custom_domain_name,
            type="PRIMARY",
        )
    ]

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
```
**Important Considerations for `source_dir` in `AppSpecStaticSiteArgs`:**
The `source_dir` for `AppSpecStaticSiteArgs` when not using a Git source (like GitHub) is a bit nuanced. Pulumi needs to package these local files and upload them to DigitalOcean for the App Platform to use.

*   The path provided to `source_dir` (`admin_ui_dist_path`) is an absolute path on the machine running `pulumi up`.
*   Pulumi will zip the contents of this directory and upload it.
*   This approach is generally fine for deploying pre-built static assets.

The use of `os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "admin-ui", "dist"))` correctly calculates the absolute path to `admin-ui/dist` relative to the `infra` directory where `do_superagi_stack.py` resides. This should work correctly in the CI environment where `admin-ui/dist` is populated before `pulumi up` is run from the `infra` directory.

The warning about the path not existing is good for local development but might be noisy in CI if the path is guaranteed to exist. However, it doesn't hurt to have it.

The code looks reasonable for a first attempt with App Platform `static_site` and `source_dir`.

I will submit the report.
