# Cursor IaC Agent Mode Setup

This guide outlines how to enable a specialized Infrastructure-as-Code agent in Cursor IDE for Orchestra AI.

## 1. Base Configuration
- Upgrade to **Cursor Pro** for advanced IaC features (already enabled).
- Install Pulumi and required Python packages in your workspace.
- Grant GitHub read/write access to repositories and configure branch protection exemptions for the agent.

## 2. IaC Rules
Create `.cursor/rules/iac.mdc` with Pulumi standards:
- Lambda Labs stack configuration and tagging rules
- Security baseline for PostgreSQL and Redis
- Auto-generated component READMEs

## 3. Agent Profile
Add `.cursor/agents/iac_agent.yaml`:
```yaml
name: IaC Specialist
system_prompt: |
  You are an expert infrastructure engineer specializing in Pulumi.
  Focus on Lambda Labs Cloud with Weaviate, Pinecone, PostgreSQL and Redis integrations.

tools:
  - pulumi_preview
  - cloud_cost_calculator
  - security_scanner
constraints:
  max_parallel_env: 3
  approval_threshold: medium_risk
```

## 4. Background Environment
Place the Dockerfile and runtime config in `.cursor/environment/`:
```Dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    pulumi=3.50.0 \
    python3-pip

RUN pip3 install \
    weaviate-client \
    pinecone-client \
    psycopg2-binary \
    redis
```
```json
{
  "pre_commands": ["pulumi stack select dev"],
  "post_commands": ["pulumi preview"]
}
```

## 5. Workflow Automation
Example command in Cursor chat:
```
"Create autoscaling group with blue/green deployment pattern for ECS cluster"
```
The agent generates Pulumi components, configures infrastructure and runs previews in a staging stack.

## 6. Security and Testing
Use `.cursor/secrets.yaml` for encrypted variables and define access controls in `cursor-permissions.json`. Each agent run automatically validates Pulumi stacks, checks policies, simulates costs and produces a security report.

## 7. Approval Gates
Critical resources such as database instances can require manual approval via `.cursor/approvals.yaml`, and monthly cost thresholds can be enforced.

This configuration enables reliable Pulumi automation with Lambda Labs Cloud while keeping security and cost in check.
