# Placeholder for a reusable Pulumi component for Cloud Run services
import pulumi
import pulumi_gcp as gcp


class CloudRunServiceComponent(pulumi.ComponentResource):
    def __init__(self, name, image_name, opts=None):
        super().__init__("custom:resource:CloudRunServiceComponent", name, {}, opts)
        # ... logic to create Cloud Run service ...
        self.url = pulumi.Output.concat("https-", name, "-uc.a.run.app")  # Placeholder URL
        pulumi.export(f"{name}_url", self.url)
