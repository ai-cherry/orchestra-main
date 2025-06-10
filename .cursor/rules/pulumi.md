---
description: Pulumi Infrastructure as Code patterns for Lambda Labs Cloud deployment
globs: ["infrastructure/**/*.py", "**/__main__.py", "**/Pulumi.yaml", "**/Pulumi.*.yaml"]
autoAttach: true
priority: high
---

# Pulumi Lambda Labs Infrastructure Standards

## Resource Organization
- **Stack structure**: Environment-specific stacks (dev, staging, production)
- **Component patterns**: Group related resources into reusable Pulumi Components
- **Naming conventions**: `{project}-{environment}-{service}-{resource-type}`
- **Tagging strategy**: Environment, Project, Owner, CostCenter tags mandatory

## Lambda Labs VPS Optimization
- **Instance sizing**: CPU/memory/storage based on workload analysis
- **Startup scripts**: Include comprehensive initial configuration
- **Security groups**: Minimal required permissions, explicit deny default
- **SSH key management**: Rotate keys through Pulumi configuration

## Configuration Management
- **Secrets handling**: Use `pulumi.Output.secret()` for sensitive data
- **Environment variables**: Stack-specific config for deployment variations
- **Config validation**: Type checking and constraint validation at deploy time
- **State backend**: Local filesystem or S3-compatible for team access

## Deployment Patterns
- **Idempotent operations**: All stacks must handle re-deployment gracefully
- **Rollback procedures**: Automated rollback on deployment failure
- **Cost estimation**: Preview mode for infrastructure cost analysis
- **Dependency management**: Explicit resource dependencies, avoid implicit ordering

## Integration Requirements
- **GitHub secrets**: Store API keys in organization-level secrets
- **Monitoring setup**: CloudWatch/monitoring agents in startup scripts
- **Backup automation**: Database and critical data backup strategies
- **Security scanning**: Automated vulnerability assessment integration

## Performance Optimization
- **Resource right-sizing**: Monitor and adjust based on actual usage
- **Network optimization**: Regional placement for latency reduction
- **Auto-scaling patterns**: Predictive scaling based on usage patterns
- **Cost monitoring**: Budget alerts and cost optimization automation 