"""
Pulumi DigitalOcean Stack for SuperAGI & AI Orchestra
Automates Droplet provisioning, Docker setup, and SuperAGI deployment for dev/prod environments.
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

# --- CONFIGURATION ---
config = Config()
env = config.require("env")  # "dev" or "prod"
droplet_size = config.get("droplet_size") or (
    "s-1vcpu-2gb" if env == "dev" else "s-2vcpu-4gb"
)
region = config.get("region") or "sfo2"
hostname = config.get("hostname") or (
    f"superagi-{env}-sfo2-01"
    if env == "dev"
    else "ubuntu-s-2vcpu-8gb-160gb-intel-sfo2-01"
)
# SSH authentication – either pubkey+private key or root password

root_password = config.get_secret("root_password")
ssh_pubkey = config.get("ssh_pubkey")  # Optional path to SSH public key
ssh_private_key = config.get_secret("ssh_private_key")

# --- SECRETS ---
dragonfly_uri = config.require_secret("dragonfly_uri")
mongo_uri = config.require_secret("mongo_uri")
weaviate_url = config.require_secret("weaviate_url")
weaviate_api_key = config.require_secret("weaviate_api_key")
superagi_image = config.get("superagi_image") or "superagi/superagi:latest"

# --- SSH KEY RESOURCE ---
# Register an SSH key only if a pubkey path is supplied
ssh_key = None
if ssh_pubkey:
    ssh_key = do.SshKey(
        f"{env}-ssh-key", name=f"{env}-ssh-key", public_key=open(ssh_pubkey).read()
    )

# --- DROPLET ---
# --- CLOUD-INIT SCRIPT FOR DOCKER & PYTHON ---
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
    ssh_keys=[ssh_key.fingerprint] if ssh_key else [],
    tags=[f"superagi-{env}"],
    user_data=cloud_init,  # Pass cloud-init script directly
)


# --- REMOTE COMMAND: RUN SUPERAGI DOCKER CONTAINER ---
connection_args = command.remote.ConnectionArgs(
    host=droplet.ipv4_address.apply(lambda ip: ip),
    user="root",
)

if root_password:
    connection_args = command.remote.ConnectionArgs(
        host=droplet.ipv4_address.apply(lambda ip: ip),
        user="root",
        password=root_password,
    )
elif ssh_private_key:
    connection_args = command.remote.ConnectionArgs(
        host=droplet.ipv4_address.apply(lambda ip: ip),
        user="root",
        private_key=ssh_private_key,
    )

run_superagi = command.remote.Command(
    f"run-superagi-{env}",
    connection=connection_args,
    create=f"""
docker run -d --restart unless-stopped -p 8080:8080 \\
  -e DRAGONFLY_URI={dragonfly_uri} \\
  -e MONGO_URI={mongo_uri} \\
  -e WEAVIATE_URL={weaviate_url} \\
  -e WEAVIATE_API_KEY={weaviate_api_key} \\
  {superagi_image}
""",
    opts=pulumi.ResourceOptions(depends_on=[droplet]),
)

# --- FIREWALL ---
firewall = do.Firewall(
    f"superagi-{env}-firewall",
    name=f"superagi-{env}-firewall",
    droplet_ids=[droplet.id],
    inbound_rules=[
        do.FirewallInboundRuleArgs(
            protocol="tcp",
            port_range="8080",
            sources=do.FirewallInboundRuleSourcesArgs(addresses=["0.0.0.0/0"]),
        ),
        do.FirewallInboundRuleArgs(
            protocol="tcp",
            port_range="22",
            sources=do.FirewallInboundRuleSourcesArgs(addresses=["0.0.0.0/0"]),
        ),
    ],
    outbound_rules=[
        do.FirewallOutboundRuleArgs(
            protocol="tcp",
            port_range="all",
            destinations=do.FirewallOutboundRuleDestinationsArgs(
                addresses=["0.0.0.0/0"]
            ),
        ),
        do.FirewallOutboundRuleArgs(
            protocol="udp",
            port_range="all",
            destinations=do.FirewallOutboundRuleDestinationsArgs(
                addresses=["0.0.0.0/0"]
            ),
        ),
    ],
)

# --- OUTPUTS ---
pulumi.export("droplet_ip", droplet.ipv4_address)
pulumi.export("superagi_url", Output.concat("http://", droplet.ipv4_address, ":8080"))
pulumi.export("hostname", droplet.name)
