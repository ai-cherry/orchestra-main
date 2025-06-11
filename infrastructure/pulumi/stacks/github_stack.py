#!/usr/bin/env python3
"""
GitHub Infrastructure Stack - AI Orchestra
Manages GitHub repositories, branch protection, secrets, and CI/CD
Performance-optimized with Pulumi ESC integration
"""

import pulumi
import pulumi_github as github
from pulumi import Config, Output
from typing import Dict, List

# ESC Configuration
config = Config()

# Get values from ESC environment
github_token = config.require_secret("secrets:github_token")
project_name = config.require("project:name")
environment = config.require("environment")

# Performance settings
auto_scaling = config.get_bool("performance:auto_scaling") or True

print(f"🐙 Deploying GitHub infrastructure for {project_name} ({environment})")

# GitHub Provider with ESC token
github_provider = github.Provider("github",
    token=github_token,
    owner="ai-cherry"
)

# Main repository management
main_repository = github.Repository("orchestra-main",
    name="orchestra-main",
    description="AI Orchestra - Unified AI Agent Management Platform",
    visibility="private",
    has_issues=True,
    has_projects=True,
    has_wiki=False,
    has_downloads=True,
    has_discussions=True,
    delete_branch_on_merge=True,
    allow_squash_merge=True,
    allow_merge_commit=False,
    allow_rebase_merge=True,
    vulnerability_alerts=True,
    allow_auto_merge=True,
    auto_init=False,
    topics=[
        "ai", "orchestra", "mcp", "pulumi", "infrastructure",
        "automation", "lambda-labs", "vector-database"
    ],
    opts=pulumi.ResourceOptions(provider=github_provider)
)

# Branch protection for main
main_branch_protection = github.BranchProtection("main-protection",
    repository_id=main_repository.node_id,
    pattern="main",
    enforce_admins=False,  # Performance: Allow admin bypass for faster iterations
    required_status_checks=github.BranchProtectionRequiredStatusChecksArgs(
        strict=True,
        contexts=[
            "ci/python-lint",
            "ci/python-test", 
            "ci/javascript-lint",
            "ci/docker-build"
        ]
    ),
    required_pull_request_reviews=github.BranchProtectionRequiredPullRequestReviewsArgs(
        required_approving_review_count=1,
        dismiss_stale_reviews=True,
        restrict_dismissals=False,  # Performance: Allow faster review cycles
        require_code_owner_reviews=False,  # Performance: Streamlined reviews
        bypass_pull_request_allowances=github.BranchProtectionRequiredPullRequestReviewsBypassPullRequestAllowancesArgs(
            apps=["dependabot", "renovate"]
        )
    ),
    allows_deletions=False,
    allows_force_pushes=False,
    blocks_creations=False,
    opts=pulumi.ResourceOptions(
        provider=github_provider,
        depends_on=[main_repository]
    )
)

# Development branch protection (lighter for faster development)
dev_branch_protection = github.BranchProtection("dev-protection",
    repository_id=main_repository.node_id,
    pattern="develop",
    enforce_admins=False,
    required_status_checks=github.BranchProtectionRequiredStatusChecksArgs(
        strict=False,  # Performance: Allow faster merges to dev
        contexts=["ci/python-lint"]  # Minimal checks for dev
    ),
    opts=pulumi.ResourceOptions(
        provider=github_provider,
        depends_on=[main_repository]
    )
)

# GitHub Actions secrets (performance-critical infrastructure keys)
secrets_to_create = {
    "LAMBDA_API_KEY": config.require_secret("secrets:lambda_api_key"),
    "VERCEL_TOKEN": config.require_secret("secrets:vercel_token"),
    "PULUMI_ACCESS_TOKEN": config.require_secret("secrets:pulumi_access_token"),
    "OPENAI_API_KEY": config.require_secret("secrets:openai_api_key"),
    "ANTHROPIC_API_KEY": config.require_secret("secrets:anthropic_api_key"),
    "WEAVIATE_API_KEY": config.require_secret("secrets:weaviate_api_key"),
    "PINECONE_API_KEY": config.require_secret("secrets:pinecone_api_key"),
}

github_secrets = {}
for secret_name, secret_value in secrets_to_create.items():
    github_secrets[secret_name] = github.ActionsSecret(
        f"secret-{secret_name.lower().replace('_', '-')}",
        repository=main_repository.name,
        secret_name=secret_name,
        plaintext_value=secret_value,
        opts=pulumi.ResourceOptions(
            provider=github_provider,
            depends_on=[main_repository]
        )
    )

# Repository environments for deployment gates
environments = ["development", "staging", "production"]
github_environments = {}

for env_name in environments:
    github_environments[env_name] = github.RepositoryEnvironment(
        f"env-{env_name}",
        repository=main_repository.name,
        environment=env_name,
        wait_timer=30 if env_name == "production" else 0,  # Production gate
        can_admins_bypass=True,  # Performance: Allow admin bypass
        opts=pulumi.ResourceOptions(
            provider=github_provider,
            depends_on=[main_repository]
        )
    )

# Webhooks for real-time integration
webhook_urls = {
    "deployment": f"https://api.{config.require('domain')}/webhooks/deployment",
    "ci_status": f"https://api.{config.require('domain')}/webhooks/ci-status"
}

webhooks = {}
for webhook_name, webhook_url in webhook_urls.items():
    webhooks[webhook_name] = github.RepositoryWebhook(
        f"webhook-{webhook_name}",
        repository=main_repository.name,
        configuration=github.RepositoryWebhookConfigurationArgs(
            url=webhook_url,
            content_type="json",
            insecure_ssl=False
        ),
        events=[
            "push",
            "pull_request", 
            "deployment",
            "deployment_status",
            "check_run",
            "workflow_run"
        ],
        active=True,
        opts=pulumi.ResourceOptions(
            provider=github_provider,
            depends_on=[main_repository]
        )
    )

# Repository collaborators (if specified)
collaborators = config.get_object("collaborators") or []
repo_collaborators = {}

for collaborator in collaborators:
    username = collaborator.get("username")
    permission = collaborator.get("permission", "push")
    
    if username:
        repo_collaborators[username] = github.RepositoryCollaborator(
            f"collaborator-{username}",
            repository=main_repository.name,
            username=username,
            permission=permission,
            opts=pulumi.ResourceOptions(
                provider=github_provider,
                depends_on=[main_repository]
            )
        )

# Performance: Create deploy keys for faster CI/CD
deploy_key = github.RepositoryDeployKey("ci-deploy-key",
    repository=main_repository.name,
    title="CI/CD Deploy Key",
    key=config.require_secret("secrets:deploy_key_public"),
    read_only=False,  # Allow pushes for automated updates
    opts=pulumi.ResourceOptions(
        provider=github_provider,
        depends_on=[main_repository]
    )
)

# Repository labels for AI-driven issue management
ai_labels = [
    {"name": "ai-enhancement", "color": "0052cc", "description": "AI-driven improvement"},
    {"name": "infrastructure", "color": "d4c5f9", "description": "Infrastructure changes"},
    {"name": "performance", "color": "ff6b6b", "description": "Performance optimization"},
    {"name": "mcp-server", "color": "4ecdc4", "description": "MCP server related"},
    {"name": "pulumi", "color": "ffd93d", "description": "Pulumi infrastructure"},
    {"name": "cursor-ai", "color": "6BCF7F", "description": "Cursor AI integration"},
]

repo_labels = {}
for label_info in ai_labels:
    repo_labels[label_info["name"]] = github.IssueLabel(
        f"label-{label_info['name']}",
        repository=main_repository.name,
        name=label_info["name"],
        color=label_info["color"],
        description=label_info["description"],
        opts=pulumi.ResourceOptions(
            provider=github_provider,
            depends_on=[main_repository]
        )
    )

# Exports for other stacks and monitoring
pulumi.export("repository_id", main_repository.id)
pulumi.export("repository_node_id", main_repository.node_id)
pulumi.export("repository_full_name", main_repository.full_name)
pulumi.export("repository_clone_url", main_repository.clone_url)
pulumi.export("repository_ssh_url", main_repository.ssh_clone_url)
pulumi.export("repository_html_url", main_repository.html_url)

# Environment URLs for integration
environment_urls = {env: github_environments[env].url for env in environments}
pulumi.export("environment_urls", environment_urls)

# Webhook URLs for monitoring
webhook_urls_export = {name: webhook.url for name, webhook in webhooks.items()}
pulumi.export("webhook_urls", webhook_urls_export)

# Performance metrics
pulumi.export("github_stack_config", {
    "auto_scaling": auto_scaling,
    "environment": environment,
    "project": project_name,
    "secrets_count": len(secrets_to_create),
    "environments_count": len(environments),
    "webhooks_count": len(webhooks)
})

print(f"✅ GitHub infrastructure deployed for {project_name} ({environment})")
print(f"📊 Created {len(secrets_to_create)} secrets, {len(environments)} environments, {len(webhooks)} webhooks") 