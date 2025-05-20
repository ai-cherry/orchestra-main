# Placeholder for shared Pulumi configuration logic
import pulumi


def get_stack_config():
    config = pulumi.Config()
    return {
        "gcp_project": config.require("gcp:project"),
        "gcp_region": config.require("gcp:region"),
    }
