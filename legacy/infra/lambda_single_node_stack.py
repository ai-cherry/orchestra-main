import pulumi
from pulumi import Config
from components.Lambda_server_component import LambdaServerComponent

config = Config()
env = config.require("env")
ssh_keys = config.get("ssh_key_ids")

server = LambdaServerComponent(
    "cherry_ai-Lambda",
    {
        "plan": config.get("plan") or "vhp-16c-64gb",
        "region": config.get("region") or "ewr",
        "os_id": config.get_int("os_id") or 215,
        "volume_size_gb": config.get_int("volume_size_gb") or 500,
        "ssh_key_ids": ssh_keys.split(",") if ssh_keys else None,
        "ssh_private_key": config.get_secret("ssh_private_key"),
    },
)

if env == "dev":
    pulumi.export("LAMBDA_SERVER_IP", server.ip)
