"""
Lambda Labs Infrastructure for Orchestra Project
Main Pulumi program for provisioning Lambda Labs instances
"""

import pulumi
from lambda_labs_infrastructure import LambdaLabsInstance

# Get configuration
config = pulumi.Config()
instance_name = config.get("lambda:instance_name") or "orchestra-dev"
ssh_key_id = config.require_int("lambda:ssh_key_id")

# Create Lambda Labs instance
instance = LambdaLabsInstance(
    instance_name,
    {
        "instance_type": config.get("lambda:instance_type") or "gpu_1x_a10",
        "region": config.get("lambda:region") or "us-west-1",
        "ssh_key_ids": [ssh_key_id]
    }
)

# Export outputs
pulumi.export("instance_id", instance.instance_id)
pulumi.export("ip_address", instance.ip_address)
pulumi.export("ssh_command", instance.ip_address.apply(lambda ip: f"ssh ubuntu@{ip}"))
pulumi.export("vscode_command", instance.ip_address.apply(
    lambda ip: f"code --remote ssh-remote+ubuntu@{ip} /home/ubuntu/orchestra-main"
))