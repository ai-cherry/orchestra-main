"""Pulumi program for deploying the AI Agent infrastructure on GCP."""

import pulumi
import pulumi_gcp as gcp

# 0. Constants
AGENT_DOCKER_REPOSITORY_ID = "agent-docker"
AI_AGENT_SERVICE_NAME = "ai-agent"
OPENAI_API_KEY_SECRET_NAME = "OPENAI_API_KEY"
PORTKEY_API_KEY_SECRET_NAME = "PORTKEY_API_KEY"
DASHBOARD_DOCKER_REPOSITORY_ID = "dashboard-docker"
AI_DASHBOARD_SERVICE_NAME = "ai-dashboard"

# 1. Configuration
config = pulumi.Config()
gcp_config = pulumi.Config("gcp")

project_id = gcp_config.require("project")
region = gcp_config.require("region")

# TODO: Define agentImageUrl in Pulumi config (e.g., Pulumi.dev.yaml or via `pulumi config set agentImageUrl ...`)
# This should be the full path to the image in Artifact Registry.
# Example: infra:agentImageUrl: "us-docker.pkg.dev/your-project-id/agent-docker/your-agent-image:tag"
agent_image_url = config.require("agentImageUrl")

# TODO: Define dashboardImageUrl in Pulumi config (e.g., Pulumi.dev.yaml or via `pulumi config set dashboardImageUrl ...`)
# This should be the full path to the image in Artifact Registry.
# Example: infra:dashboardImageUrl: "us-docker.pkg.dev/your-project-id/dashboard-docker/your-dashboard-image:tag"
dashboard_image_url = config.require("dashboardImageUrl")

pulumi.log.info(
    f"Using Project ID: {project_id}, Region: {region}, Agent Image URL: {agent_image_url}, Dashboard Image URL: {dashboard_image_url}"
)

# 2. Artifact Registry Repositories
# This repository will store the Docker images for the AI agent.
agent_artifact_repo = gcp.artifactregistry.Repository(
    "agentDockerRepo",
    repository_id=AGENT_DOCKER_REPOSITORY_ID,  # Use constant
    project=project_id,
    location=region,
    format="DOCKER",
    description="Docker repository for AI agent images.",
)

# New Artifact Registry repository for the Dashboard service
dashboard_artifact_repo = gcp.artifactregistry.Repository(
    "dashboardDockerRepo",
    repository_id=DASHBOARD_DOCKER_REPOSITORY_ID,
    project=project_id,
    location=region,
    format="DOCKER",
    description="Docker repository for AI dashboard images.",
)

# 3. Secret Manager Secrets
# These resources define the secrets in GCP Secret Manager.
# The actual secret values (versions) must be added manually or through a separate secure process.

openai_api_key_secret = gcp.secretmanager.Secret(
    "openaiApiKeySecret",
    secret_id=OPENAI_API_KEY_SECRET_NAME,  # Use constant
    project=project_id,
    replication=gcp.secretmanager.SecretReplicationArgs(
        automatic=True,
    ),
)
# TODO: Ensure the 'OPENAI_API_KEY' secret has a version with the actual API key in GCP Secret Manager.

portkey_api_key_secret = gcp.secretmanager.Secret(
    "portkeyApiKeySecret",
    secret_id=PORTKEY_API_KEY_SECRET_NAME,  # Use constant
    project=project_id,
    replication=gcp.secretmanager.SecretReplicationArgs(
        automatic=True,
    ),
)
# TODO: Ensure the 'PORTKEY_API_KEY' secret has a version with the actual API key in GCP Secret Manager.
# TODO: If the agent needs PORTKEY_API_KEY, add it as an environment variable to the Cloud Run service below.

# 4. Cloud Run GPU Service for AI Agent
ai_agent_service = gcp.cloudrunv2.Service(
    "aiAgentService",
    name=AI_AGENT_SERVICE_NAME,  # Use constant
    project=project_id,
    location=region,
    template=gcp.cloudrunv2.ServiceTemplateArgs(
        annotations={
            # Request L4 GPU, as specified (Beta)
            "run.googleapis.com/accelerator": "nvidia-l4",
            # TODO: Consider adding min/max instances for scaling, e.g.:
            # "autoscaling.knative.dev/minScale": "0", # For dev/cost savings
            # "autoscaling.knative.dev/maxScale": "3", # Example max instances
        },
        containers=[
            gcp.cloudrunv2.ServiceTemplateContainerArgs(
                image=agent_image_url,  # From Pulumi config
                resources=gcp.cloudrunv2.ServiceTemplateContainerResourcesArgs(
                    limits={
                        "cpu": "4",  # 4 vCPU, as specified
                        "memory": "16Gi",  # 16 GiB Memory, as specified
                        # GPU count is implicitly 1 with the "nvidia-l4" accelerator.
                    },
                    # startup_cpu_boost=True, # Optional: can improve cold start times
                ),
                envs=[
                    gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                        name="OPENAI_API_KEY",
                        value_source=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                            secret_key_ref=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                secret=openai_api_key_secret.secret_id,  # References "OPENAI_API_KEY" secret
                                version="latest",  # Use the latest version of the secret
                            ),
                        ),
                    ),
                    # TODO: Add environment variable for PORTKEY_API_KEY if needed by the agent:
                    # gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                    #     name="PORTKEY_API_KEY",
                    #     value_source=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                    #         secret_key_ref=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                    #             secret=portkey_api_key_secret.secret_id,
                    #             version="latest",
                    #         ),
                    #     ),
                    # ),
                    # TODO: Add any other necessary environment variables (e.g., configuration values).
                ],
                ports=[
                    gcp.cloudrunv2.ServiceTemplateContainerPortArgs(
                        # Assuming the agent application listens on port 8080. Adjust if different.
                        container_port=8080
                    )
                ],
            )
        ],
        # execution_environment="EXECUTION_ENVIRONMENT_GEN2", # Gen 2 is typically required for GPUs and often default
        # timeout="300s", # Default is 5 minutes. Adjust if longer processing times are needed.
        # TODO: If not using the default compute service account, specify a dedicated one:
        # service_account="your-service-account-email@your-project-id.iam.gserviceaccount.com",
    ),
)

# New Cloud Run Service for AI Dashboard
ai_dashboard_service = gcp.cloudrunv2.Service(
    "aiDashboardService",
    name=AI_DASHBOARD_SERVICE_NAME,
    project=project_id,
    location=region,
    template=gcp.cloudrunv2.ServiceTemplateArgs(
        # annotations: {} # Add if any specific annotations needed for dashboard
        containers=[
            gcp.cloudrunv2.ServiceTemplateContainerArgs(
                image=dashboard_image_url,  # From Pulumi config
                resources=gcp.cloudrunv2.ServiceTemplateContainerResourcesArgs(
                    limits={
                        "cpu": "1",  # Standard CPU, adjust as needed
                        "memory": "1Gi",  # Standard memory, adjust as needed
                    }
                ),
                envs=[
                    gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                        name="NEXT_PUBLIC_DASHBOARD_API_URL",  # Env var for Next.js frontend
                        value=ai_agent_service.uri,  # Dynamically set to the agent's URL
                    ),
                    # Add other necessary environment variables for the dashboard here
                ],
                ports=[
                    gcp.cloudrunv2.ServiceTemplateContainerPortArgs(
                        container_port=3000  # Default Next.js port
                    )
                ],
            )
        ],
        # execution_environment="EXECUTION_ENVIRONMENT_GEN2",
        # timeout="60s", # Default is 5 minutes. Adjust if needed.
        # service_account: Specify if not default
    ),
)

# 5. Allow Unauthenticated Invocations
# This IAM policy makes the Cloud Run service publicly accessible.
# Review carefully if this is the desired state for your service.
cloud_run_invoker_binding = gcp.cloudrunv2.ServiceIamPolicy(
    "aiAgentPublicAccess",
    project=project_id,  # Explicitly set project
    location=region,  # Explicitly set region
    name=ai_agent_service.name,  # Use the output name of the service
    policy_data=pulumi.Output.json_dumps(
        {
            "bindings": [
                {
                    "role": "roles/run.invoker",
                    # Grants invocation permission to anyone
                    "members": ["allUsers"],
                }
            ]
        }
    ),
)

# IAM policy for public access to the Dashboard service
dashboard_public_access = gcp.cloudrunv2.ServiceIamPolicy(
    "aiDashboardPublicAccess",
    project=project_id,
    location=region,
    name=ai_dashboard_service.name,
    policy_data=pulumi.Output.json_dumps(
        {
            "bindings": [
                {
                    "role": "roles/run.invoker",
                    "members": ["allUsers"],
                }
            ]
        }
    ),
)

# 6. Exports
# Export the URL of the deployed Cloud Run service.
pulumi.export("ai_agent_service_url", ai_agent_service.uri)

# Export the Artifact Registry repository URL.
pulumi.export(
    "artifact_registry_repository_url",
    pulumi.Output.concat(
        f"{region}-docker.pkg.dev/{project_id}/{agent_artifact_repo.repository_id}"
    ),
)

# Export the Dashboard Artifact Registry repository URL.
pulumi.export(
    "dashboard_artifact_registry_repository_url",
    pulumi.Output.concat(
        f"{region}-docker.pkg.dev/{project_id}/{dashboard_artifact_repo.repository_id}"
    ),
)

# Export the URL of the deployed Dashboard service.
pulumi.export("ai_dashboard_service_url", ai_dashboard_service.uri)

# TODO: After running `pulumi up`, ensure that:
#   1. The `OPENAI_API_KEY` and `PORTKEY_API_KEY` secrets in GCP Secret Manager are populated with actual values.
#   2. The `agentImageUrl` and `dashboardImageUrl` in your Pulumi stack configuration (e.g., `Pulumi.dev.yaml`) point to valid Docker images
#      pushed to the created Artifact Registry repositories.
#      Example for agent: `pulumi config set agentImageUrl us-central1-docker.pkg.dev/your-gcp-project/agent-docker/your-image:tag`
#      Example for dashboard: `pulumi config set dashboardImageUrl us-central1-docker.pkg.dev/your-gcp-project/dashboard-docker/your-image:tag`
#   3. Project and region are configured:
#      `pulumi config set gcp:project YOUR_PROJECT_ID`
#      `pulumi config set gcp:region YOUR_REGION`
