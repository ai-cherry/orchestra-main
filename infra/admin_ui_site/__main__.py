"""Admin UI Static Site Pulumi Program"""

import pulumi
from __init__ import AdminUiSite

# Get configuration
config = pulumi.Config()
domain_name = config.require("domainName")

# Create the static site infrastructure
site = AdminUiSite("admin-ui", domain_name=domain_name)

# Export outputs
pulumi.export("bucket_name", site.bucket_name)
pulumi.export("lb_ip_address", site.lb_ip_address)
pulumi.export("site_url", pulumi.Output.concat("https://", domain_name))
