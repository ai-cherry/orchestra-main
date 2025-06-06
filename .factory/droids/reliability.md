# Factory AI Reliability Droid

## Overview
The Reliability Droid specializes in deployment, monitoring, and infrastructure management. It ensures systems are reliable, scalable, and maintainable in production environments.

## Capabilities
- **Deployment Automation**: Creates and manages deployment pipelines
- **Infrastructure as Code**: Develops Pulumi/Pulumi configurations
- **Monitoring Setup**: Implements comprehensive monitoring solutions
- **Incident Response**: Provides runbooks and automated remediation
- **Capacity Planning**: Analyzes and predicts resource needs

## Integration with Roo
- Maps to: `deployment_server.py`
- Context sharing: Infrastructure state, deployment history, metrics
- Fallback: Roo's deployment tools handle requests if Factory AI is unavailable

## Request Format
```json
{
  "droid": "reliability",
  "task": "deploy|monitor|scale|remediate",
  "context": {
    "application": {
      "name": "string",
      "version": "string",
      "dependencies": ["array"]
    },
    "infrastructure": {
      "provider": "Lambda|aws|gcp",
      "region": "string",
      "resources": "object"
    },
    "requirements": {
      "availability": "99.9%",
      "scalability": "object",
      "compliance": ["array"]
    }
  },
  "options": {
    "deployment_strategy": "blue-green|canary|rolling",
    "monitoring_level": "basic|standard|comprehensive",
    "auto_scaling": true
  }
}
```

## Response Format
```json
{
  "deployment": {
    "strategy": "object",
    "pipeline": "object",
    "rollback_plan": "object"
  },
  "infrastructure": {
    "pulumi_code": "string",
    "resource_definitions": "object",
    "cost_estimate": "object"
  },
  "monitoring": {
    "metrics": ["array"],
    "alerts": ["array"],
    "dashboards": "object"
  },
  "reliability_report": {
    "sla_compliance": "object",
    "risk_assessment": "object",
    "recommendations": ["array"]
  }
}
```

## Performance Characteristics
- Average response time: 3-6 seconds
- Token usage: 2000-5000 per request
- Caching: Infrastructure templates cached for 6 hours
- Concurrency: Supports up to 5 parallel deployments

## Best Practices
1. Define clear SLAs and reliability targets
2. Implement comprehensive monitoring from day one
3. Use infrastructure as code for all resources
4. Plan for failure with robust rollback strategies
5. Automate incident response where possible

## Deployment Strategies
- **Blue-Green**: Zero-downtime deployments with instant rollback
- **Canary**: Gradual rollout with automated rollback on errors
- **Rolling**: Sequential updates with health checks
- **Feature Flags**: Decouple deployment from release

## Monitoring Stack
- **Metrics**: Prometheus + Grafana
- **Logs**: ELK Stack or similar
- **Traces**: Jaeger or OpenTelemetry
- **Alerts**: PagerDuty integration
- **Status**: Public status page

## Infrastructure Standards
- **Lambda**: Optimized for cost-effective scaling
- **Pulumi**: TypeScript/Python for infrastructure
- **Security**: Zero-trust networking, encryption at rest
- **Backup**: Automated backups with tested restore
- **Disaster Recovery**: Multi-region failover capability