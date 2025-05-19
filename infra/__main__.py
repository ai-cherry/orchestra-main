import pulumi
import pulumi_gcp as gcp

# Configuration
config = pulumi.Config()
project = gcp.config.project
region = gcp.config.region if gcp.config.region else "us-central1"

# --- Cloud Workstations ---
# Create a workstation cluster
workstation_cluster = gcp.workstations.WorkstationCluster("default",
                                                          project=project,
                                                          location=region,
                                                          workstation_cluster_id="workstation-cluster",
                                                          network="default",  # Assumes a 'default' VPC network exists
                                                          subnetwork="default")  # Assumes a 'default' subnetwork in the 'default' VPC

# Create a workstation config
workstation_config = gcp.workstations.WorkstationConfig("default",
                                                        project=project,
                                                        location=region,
                                                        workstation_cluster_id=workstation_cluster.workstation_cluster_id,
                                                        workstation_config_id="workstation-config",
                                                        idle_timeout="7200s",  # 2 hours
                                                        running_timeout="14400s",  # 4 hours
                                                        host={
                                                            "gce_instance": {
                                                                "machine_type": "e2-standard-4",  # Example machine type
                                                                "boot_disk_size_gb": 50,
                                                                "disable_public_ip_addresses": False,
                                                            }
                                                        })

# Note: Provisioning an actual workstation instance would typically be done by a user,
# not automated here, as it's user-specific. This sets up the cluster and config.
pulumi.export("workstation_cluster_name", workstation_cluster.name)
pulumi.export("workstation_config_name", workstation_config.name)

# --- Cloud Run ---
# Assume a Docker image is already built and available in Google Artifact Registry
# e.g., gcr.io/PROJECT_ID/my-app:latest or REGION-docker.pkg.dev/PROJECT_ID/REPO/my-app:latest
# You'll need to replace this with your actual image path
cloud_run_image_name = config.require("cloudRunImage")

# Create a Cloud Run service
cloud_run_service = gcp.cloudrunv2.Service("default-service",
                                           project=project,
                                           location=region,
                                           template={
                                               "scaling": {
                                                   "max_instance_count": 2,  # Adjust as needed
                                               },
                                               "containers": [{
                                                   "image": cloud_run_image_name,
                                                   # Adjust if your app uses a different port
                                                   "ports": [{"container_port": 8080}],
                                                   # Add environment variables, secrets, etc. here
                                                   # "envs": [
                                                   #     {
                                                   #         "name": "MY_SECRET",
                                                   #         "value_source": {
                                                   #             "secret_key_ref": {
                                                   #                 "secret": "my-secret-name", # Secret Manager secret name
                                                   #                 "version": "latest"        # Secret version
                                                   #             }
                                                   #         }
                                                   #     }
                                                   # ],
                                               }],
                                           })

# Allow unauthenticated invocations (for public access)
# Remove this if you want to control access via IAM
iam_member = gcp.cloudrunv2.ServiceIamMember("allow-all",
                                             project=cloud_run_service.project,
                                             location=cloud_run_service.location,
                                             name=cloud_run_service.name,
                                             role="roles/run.invoker",
                                             member="allUsers")

pulumi.export("cloud_run_service_url", cloud_run_service.uri)
pulumi.export("cloud_run_service_name", cloud_run_service.name)

# --- Secret Manager Access for Cloud Run ---
# The default Cloud Run service account needs access to secrets it might use.
# Get the default service account for Cloud Run (format: service-PROJECT_NUMBER@gcp-sa-run.iam.gserviceaccount.com)
# This requires knowing the project number.
# Alternatively, you can specify a dedicated service account for the Cloud Run service.

# For this example, let's assume you have a secret named "my-app-secret"
# Grant the Cloud Run service (using its default SA) access to this specific secret.
# Note: You would typically get the PROJECT_NUMBER programmatically or via config.
# project_number = gcp.organizations.get_project().number # This can get the project number
# cloud_run_sa_email = pulumi.Output.concat("service-", project_number, "@gcp-sa-run.iam.gserviceaccount.com")

# For simplicity, we'll construct a role for the default compute service account if one is not specified for Cloud Run
# (which Cloud Run can use by default) or a specific service account if configured.
# If your Cloud Run service uses a specific service account, provide its email.
# e.g., my-cloud-run-sa@project-id.iam.gserviceaccount.com
cloud_run_service_account_email = config.get("cloudRunServiceAccountEmail")

# If no specific SA is provided, we assume the default compute SA for simplicity in this example.
# In a real scenario, use the actual Cloud Run service account.
# The default Compute Engine service account email is {PROJECT_NUMBER}-compute@developer.gserviceaccount.com
# For a more robust solution, use a dedicated SA for Cloud Run.

# Example: Granting Secret Accessor role to the Cloud Run service's identity
# Replace `your-secret-id` with the actual ID of the secret in Secret Manager.
secret_id_to_access = config.get("secretIdToAccess")  # e.g. "my-app-secret"

if secret_id_to_access and cloud_run_service_account_email:
    secret_accessor_binding = gcp.secretmanager.SecretIamMember("secret-accessor",
                                                                project=project,  # Project where the secret resides
                                                                secret_id=secret_id_to_access,
                                                                role="roles/secretmanager.secretAccessor",
                                                                member=pulumi.Output.concat("serviceAccount:", cloud_run_service_account_email))
    pulumi.export("secret_accessor_binding_id", secret_accessor_binding.id)

# --- Cloud Build Trigger ---
# Assumes you have a GitHub repository connected to Cloud Build.
# Replace with your repository owner and name.
github_repo_owner = config.require("githubRepoOwner")
github_repo_name = config.require("githubRepoName")

# The name of the repository as it appears in Google Cloud Source Repositories
# Format: github_OWNER_REPO
source_repo_name = pulumi.Output.concat("github_", github_repo_owner, "_", github_repo_name)

cloud_build_trigger = gcp.cloudbuild.Trigger("main-branch-push",
                                             project=project,
                                             location=region,  # Cloud Build triggers can be global or regional
                                             description="Trigger for main branch pushes",
                                             github={
                                                 "owner": github_repo_owner,
                                                 "name": github_repo_name,
                                                 "push": {
                                                     "branch": "^main$",  # Regex for the main branch
                                                 },
                                             },
                                             # Define the build steps (e.g., inline build config or reference a cloudbuild.yaml)
                                             # This example uses a simple inline build step to echo a message.
                                             # Replace with your actual build configuration.
                                             build={
                                                 "steps": [{
                                                     "name": "gcr.io/cloud-builders/docker",  # Example: using docker builder
                                                     "args": ["build", "-t", pulumi.Output.concat("gcr.io/", project, "/my-app:$COMMIT_SHA"), "."],
                                                 },
                                                     {
                                                     "name": "gcr.io/cloud-builders/docker",
                                                     "args": ["push", pulumi.Output.concat("gcr.io/", project, "/my-app:$COMMIT_SHA")],
                                                 }
                                                 ],
                                                 # Example: specify image to be built and pushed
                                                 "images": [pulumi.Output.concat("gcr.io/", project, "/my-app:$COMMIT_SHA")]
                                             }
                                             # If your source code is in a subdirectory of the repo, specify it:
                                             # included_files = ["infra/**"] # Only trigger if files in infra/ change
                                             # ignored_files = ["README.md"]
                                             )

pulumi.export("cloud_build_trigger_id", cloud_build_trigger.id)

# Pulumi requires a __main__.py for Python programs.
# Ensure you have `pulumi-gcp` plugin installed: `pulumi plugin install resource gcp v6.67.0` (or latest)
# And the Python SDK: `pip install pulumi_gcp`
