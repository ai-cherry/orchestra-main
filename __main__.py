"""Orchestra AI Infrastructure - Complete Production Deployment"""

import pulumi
import pulumi_aws as aws
import pulumi_gcp as gcp
from pulumi import Config, Output, export
import json
from typing import Dict, Any

# Get configuration
config = Config()
stack = pulumi.get_stack()
project = pulumi.get_project()

# Get all secrets from Pulumi config
secrets = {
    "github_pat": config.require_secret("github_pat"),
    "pulumi_access_token": config.require_secret("pulumi_access_token"),
    "openai_api_key": config.require_secret("openai_api_key"),
    "anthropic_api_key": config.require_secret("anthropic_api_key"),
    "notion_api_key": config.require_secret("notion_api_key"),
    "vercel_api_token": config.require_secret("vercel_api_token"),
    "pinecone_api_key": config.require_secret("pinecone_api_key"),
    "weaviate_api_key": config.require_secret("weaviate_api_key"),
    "slack_bot_token": config.require_secret("slack_bot_token"),
    "neo4j_password": config.require_secret("neo4j_password"),
}

# Additional API keys
additional_secrets = {
    "perplexity_api_key": config.get_secret("perplexity_api_key"),
    "groq_api_key": config.get_secret("groq_api_key"),
    "elevenlabs_api_key": config.get_secret("elevenlabs_api_key"),
    "deepgram_api_key": config.get_secret("deepgram_api_key"),
    "replicate_api_token": config.get_secret("replicate_api_token"),
    "huggingface_api_token": config.get_secret("huggingface_api_token"),
    "cohere_api_key": config.get_secret("cohere_api_key"),
    "ai21_api_key": config.get_secret("ai21_api_key"),
    "together_api_key": config.get_secret("together_api_key"),
    "mistral_api_key": config.get_secret("mistral_api_key"),
    "voyage_api_key": config.get_secret("voyage_api_key"),
    "jina_api_key": config.get_secret("jina_api_key"),
    "mixedbread_api_key": config.get_secret("mixedbread_api_key"),
    "nomic_api_key": config.get_secret("nomic_api_key"),
    "nvidia_api_key": config.get_secret("nvidia_api_key"),
    "fireworks_api_key": config.get_secret("fireworks_api_key"),
    "openrouter_api_key": config.get_secret("openrouter_api_key"),
    "langchain_api_key": config.get_secret("langchain_api_key"),
    "langsmith_api_key": config.get_secret("langsmith_api_key"),
    "helicone_api_key": config.get_secret("helicone_api_key"),
    "portkey_api_key": config.get_secret("portkey_api_key"),
    "unstructured_api_key": config.get_secret("unstructured_api_key"),
    "e2b_api_key": config.get_secret("e2b_api_key"),
    "browserless_api_key": config.get_secret("browserless_api_key"),
    "serper_api_key": config.get_secret("serper_api_key"),
    "serpapi_api_key": config.get_secret("serpapi_api_key"),
    "wolfram_app_id": config.get_secret("wolfram_app_id"),
    "zapier_nla_api_key": config.get_secret("zapier_nla_api_key"),
}

# Database credentials
db_secrets = {
    "postgres_password": config.get_secret("postgres_password") or "orchestra_secure_2024",
    "redis_password": config.get_secret("redis_password") or "redis_orchestra_2024",
    "neo4j_uri": config.get("neo4j_uri") or "bolt://localhost:7687",
    "neo4j_user": config.get("neo4j_user") or "neo4j",
}

# Service URLs
service_urls = {
    "notion_workspace_id": "20bdba04940280ca9ba7f9bce721f547",
    "pinecone_environment": "us-east-1",
    "weaviate_url": "https://orchestra-ai-weaviate.weaviate.network",
    "lambda_labs_api_url": "https://cloud.lambdalabs.com/api/v1",
}

# Tags for all resources
tags = {
    "Project": "Orchestra-AI",
    "Environment": stack,
    "ManagedBy": "Pulumi",
    "Version": "2.0",
}

# Create AWS resources (if AWS is configured)
if config.get("aws:region"):
    # Create S3 bucket for backups
    backup_bucket = aws.s3.Bucket("orchestra-ai-backups",
        acl="private",
        versioning=aws.s3.BucketVersioningArgs(
            enabled=True,
        ),
        server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
            rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
                apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                    sse_algorithm="AES256",
                ),
            ),
        ),
        tags=tags,
    )
    
    # Create Secrets Manager entries for API keys
    for key, value in secrets.items():
        if value:
            aws.secretsmanager.Secret(f"orchestra-ai-{key}",
                name=f"orchestra-ai/{stack}/{key}",
                description=f"Orchestra AI {key.replace('_', ' ').title()}",
                secret_string=value,
                tags=tags,
            )
    
    export("backup_bucket_name", backup_bucket.id)

# Create GCP resources (if GCP is configured)
if config.get("gcp:project"):
    # Create Cloud Storage bucket
    gcs_bucket = gcp.storage.Bucket("orchestra-ai-storage",
        location="US",
        storage_class="STANDARD",
        uniform_bucket_level_access=gcp.storage.BucketUniformBucketLevelAccessArgs(
            enabled=True,
        ),
        labels={k.lower(): v.lower().replace(" ", "-") for k, v in tags.items()},
    )
    
    export("gcs_bucket_name", gcs_bucket.name)

# Create Lambda Labs deployment configuration
lambda_labs_config = {
    "instance_type": "gpu_1x_a100",
    "region": "us-west-1",
    "ssh_key_name": "orchestra-ai-key",
    "file_system_names": ["orchestra-ai-storage"],
}

# Export all configuration for use by other tools
export("project_name", project)
export("stack_name", stack)
export("service_urls", service_urls)
export("lambda_labs_config", lambda_labs_config)

# Export status
export("infrastructure_status", {
    "pulumi_configured": True,
    "secrets_stored": len(secrets) + len([s for s in additional_secrets.values() if s]),
    "aws_enabled": config.get("aws:region") is not None,
    "gcp_enabled": config.get("gcp:project") is not None,
    "ready_for_deployment": True,
})

# Create a comprehensive configuration output
export("orchestra_config", Output.secret({
    "api_keys": {**secrets, **{k: v for k, v in additional_secrets.items() if v}},
    "database": db_secrets,
    "services": service_urls,
    "deployment": lambda_labs_config,
    "tags": tags,
}))

print(f"✅ Orchestra AI Infrastructure configured for stack: {stack}")
print(f"📦 {len(secrets)} core secrets configured")
print(f"🔐 All secrets encrypted in Pulumi Cloud")
print(f"🚀 Ready for deployment!") 