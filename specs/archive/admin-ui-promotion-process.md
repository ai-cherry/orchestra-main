# Admin UI Promotion to Production Process

This document outlines the process for promoting the Admin UI to the production environment and considerations for zero-downtime rollouts.

## Current Setup

*   **CI/CD Workflow:** The `.github/workflows/deploy.yaml` workflow handles building, testing, and deploying the Admin UI.
*   **Environments:**
    *   `dev`: Deployed automatically on pushes to the `main` branch (excluding version tags). This serves as the staging/testing environment.
    *   `prod`: Deployed on pushing a version tag (e.g., `v1.0.0`, `v1.0.1`) or via manual `workflow_dispatch`. This deployment targets a GitHub "production" environment, which should be configured with required reviewers for manual approval.
*   **Deployment Tool:** Pulumi is used for infrastructure and application deployment to the Vultr server.
*   **Admin UI Hosting:** The Admin UI files are served by Nginx on the Vultr host.
*   **Backend Services (e.g., SuperAGI):** Deployed as Docker containers on the same Vultr instance.

## Promotion Process to Production

1.  **Development & Testing on `dev`:**
    *   All new features and bug fixes are developed on feature branches and merged to `main` via Pull Requests.
    *   Each push to `main` automatically triggers the `build-and-test-admin-ui` job and, if successful, the `deploy-to-dev` job.
    *   The deployed `dev` environment (URL provided by Pulumi output `admin_ui_live_url` for the `dev` stack) is thoroughly tested using the smoke tests defined in `/specs/admin-ui-smoke-tests.md` and any other relevant QA procedures.

2.  **Decision to Promote to Production:**
    *   Once the `dev` environment is deemed stable and ready for release, a decision is made to promote to production.

3.  **Triggering Production Deployment:**
    *   **Option A (Version Tag - Recommended):** Create and push a new version tag (e.g., `git tag v1.0.0 && git push origin v1.0.0`). This automatically triggers the `deploy-to-prod` job in the CI/CD workflow.
    *   **Option B (Manual Dispatch):** Manually trigger the "Deploy Cherry AI (including Admin UI)" workflow from the GitHub Actions UI, selecting the appropriate branch/commit that has been verified on `dev`. The `deploy-to-prod` job will run based on its `workflow_dispatch` trigger.

4.  **Manual Approval (GitHub Environment):**
    *   The `deploy-to-prod` job targets the "production" GitHub environment.
    *   If this environment is configured with "Required reviewers" in the repository settings, the workflow will pause at this job, and the designated reviewers must approve the deployment in the GitHub UI.

5.  **Production Deployment Execution:**
    *   Upon approval (if configured), the `deploy-to-prod` job proceeds.
    *   It uses the same build artifact (`admin-ui-dist`) that was tested for the `dev` deployment.
    *   Pulumi selects the `prod` stack and deploys the Admin UI and any other infrastructure changes to the production environment on the Vultr server.

6.  **Post-Production Verification:**
    *   The production URL (provided by Pulumi output `admin_ui_live_url` for the `prod` stack) is tested again (e.g., a subset of smoke tests).
    *   Monitor application logs and performance.

## Zero-Downtime Rollout Considerations

*   **Admin UI (Vultr host):**
    *   Nginx serves the static files. Docker Compose performs an in-place upgrade with minimal downtime.

*   **Backend Services (e.g., SuperAGI on Droplet):**
    *   The current Pulumi script (`infra/do_superagi_stack.py`) deploys the SuperAGI Docker container to a single Droplet. This setup does **not** inherently support zero-downtime rollouts for the SuperAGI service itself.
    *   To achieve zero-downtime for backend services, a more advanced setup would be required, such as:
        *   **Blue/Green Deployments:** Provisioning a second Droplet (or set of Droplets) with the new version, testing it, and then switching traffic at a load balancer level.
        *   **Rolling Updates:** If using an conductor like Kubernetes or Docker Swarm on multiple Droplets, performing rolling updates.
        *   **Load Balancers:** Consider introducing a Vultr Load Balancer if multiple backend instances are used.
    *   These backend zero-downtime strategies are significant infrastructure changes and are currently out of scope for the Admin UI deployment but should be considered for overall platform reliability.

## Rollback Strategy

*   **Admin UI (App Platform):** App Platform often provides a mechanism to quickly roll back to previous deployments through its dashboard or CLI. Additionally, redeploying a previous Git tag via the CI/CD workflow would also constitute a rollback.
*   **Pulumi:** Pulumi state history allows for inspecting previous configurations. A rollback can be performed by checking out a previous Git commit (that contains the desired infrastructure code) and running `pulumi up` again, or by using Pulumi's explicit rollback features if available for specific changes.
*   **Backend Services:** Rollback involves redeploying a previous Docker image version for SuperAGI.

This process ensures that production deployments are intentional, approved, and leverage Nginx on Vultr for near zero downtime.
