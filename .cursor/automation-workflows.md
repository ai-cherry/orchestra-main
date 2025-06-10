# Advanced Cursor AI Automation Workflows

## Multi-Step Development Workflows

### 1. Feature Development Pipeline
```
@sequential-thinking @github @pulumi
Workflow: Full-stack feature implementation

Steps:
1. **Impact Analysis** - Identify affected services and dependencies
2. **API Design** - Define contracts and data models
3. **Infrastructure** - Assess cloud resource requirements  
4. **Backend Implementation** - API endpoints and business logic
5. **Frontend Integration** - UI components and state management
6. **Mobile Sync** - React Native compatibility and features
7. **Testing Strategy** - Unit, integration, and E2E tests
8. **Deployment Plan** - Staging and production rollout

Triggers: New feature request or epic
Output: Comprehensive implementation plan with task breakdown
```

### 2. Performance Optimization Workflow
```
@sequential-thinking @filesystem @puppeteer
Workflow: Systematic performance improvement

Steps:
1. **Profiling Setup** - Configure monitoring and measurement tools
2. **Baseline Metrics** - Capture current performance across all services
3. **Bottleneck Identification** - Database, API, frontend, infrastructure analysis
4. **Optimization Implementation** - Targeted improvements with benchmarking
5. **Regression Testing** - Ensure no functionality breaks
6. **Monitoring Configuration** - Set up alerts and dashboards
7. **Documentation Update** - Performance guidelines and runbooks

Triggers: Performance degradation alerts or optimization requests
Output: Performance improvement plan with before/after metrics
```

### 3. Security Audit Workflow
```
@sequential-thinking @github @filesystem
Workflow: Comprehensive security assessment

Steps:
1. **Code Analysis** - Static analysis for security vulnerabilities
2. **Dependency Audit** - Check for known vulnerabilities in packages
3. **Infrastructure Review** - Cloud security configuration assessment
4. **API Security** - Authentication, authorization, input validation
5. **Frontend Security** - XSS, CSRF, secure storage patterns
6. **Mobile Security** - Secure storage, API communication, biometrics
7. **Penetration Testing** - Automated and manual security testing
8. **Remediation Plan** - Prioritized fix list with implementation timeline

Triggers: Scheduled monthly audits or security incident
Output: Security assessment report with remediation roadmap
```

## Infrastructure Automation

### 4. Deployment Workflow
```
@pulumi @github @sequential-thinking
Workflow: Zero-downtime deployment pipeline

Steps:
1. **Pre-deployment Checks** - Health checks, backup verification
2. **Infrastructure Updates** - Pulumi stack changes with rollback plan
3. **Service Deployment** - Rolling updates with health monitoring
4. **Database Migrations** - Safe schema changes with rollback procedures
5. **Smoke Testing** - Critical path verification in production
6. **Performance Validation** - Response time and resource usage checks
7. **Rollback Triggers** - Automated rollback on failure conditions

Triggers: Git push to main branch or manual deployment request
Output: Deployment plan with monitoring and rollback procedures
```

### 5. Cost Optimization Workflow
```
@pulumi @sequential-thinking @filesystem
Workflow: Cloud cost analysis and optimization

Steps:
1. **Usage Analysis** - Current resource utilization and costs
2. **Right-sizing** - Instance and service optimization opportunities
3. **Resource Cleanup** - Identify unused or underutilized resources
4. **Pricing Strategy** - Reserved instances, spot instances, alternatives
5. **Architecture Review** - More cost-effective design patterns
6. **Implementation Plan** - Phased cost reduction with risk assessment
7. **Monitoring Setup** - Budget alerts and cost tracking

Triggers: Monthly cost review or budget threshold alerts
Output: Cost optimization plan with projected savings
```

## Development Automation

### 6. Code Quality Workflow
```
@github @filesystem @sequential-thinking
Workflow: Automated code quality improvement

Steps:
1. **Static Analysis** - Linting, type checking, complexity analysis
2. **Test Coverage** - Identify gaps in test coverage across projects
3. **Technical Debt** - Prioritize refactoring opportunities
4. **Documentation Audit** - Ensure code documentation completeness
5. **Performance Analysis** - Identify performance anti-patterns
6. **Security Patterns** - Enforce security best practices
7. **Improvement Plan** - Prioritized quality improvements

Triggers: Weekly scheduled runs or pre-release quality gates
Output: Code quality report with improvement recommendations
```

### 7. Dependency Management Workflow
```
@github @filesystem @sequential-thinking
Workflow: Package and dependency optimization

Steps:
1. **Vulnerability Scan** - Check for security vulnerabilities
2. **Update Analysis** - Available updates and breaking changes
3. **Compatibility Check** - Cross-project dependency compatibility
4. **Bundle Analysis** - Frontend bundle size and optimization
5. **Performance Impact** - Assess performance impact of updates
6. **Update Strategy** - Phased update plan with testing
7. **Risk Assessment** - Rollback plan for problematic updates

Triggers: Weekly dependency scans or vulnerability alerts
Output: Dependency update plan with risk mitigation
```

## Integration Workflows

### 8. Cross-Service Integration
```
@sequential-thinking @github @filesystem
Workflow: Service integration and API contract management

Steps:
1. **Contract Definition** - API specification and data models
2. **Backward Compatibility** - Ensure existing integrations continue working
3. **Testing Strategy** - Integration and contract testing setup
4. **Documentation** - API documentation and integration guides
5. **Versioning Strategy** - API versioning and deprecation timeline
6. **Monitoring Setup** - Service health and integration monitoring
7. **Rollout Plan** - Gradual integration rollout with monitoring

Triggers: New service integration or API changes
Output: Integration plan with testing and monitoring strategy
```

## Automation Configuration

### Trigger Patterns
- **Time-based**: Daily health checks, weekly quality scans, monthly security audits
- **Event-based**: Git commits, deployment requests, alert thresholds
- **Manual**: On-demand workflow execution for specific tasks
- **Conditional**: Based on metrics, thresholds, or system state

### Output Templates
- **Analysis Reports**: Structured findings with recommendations
- **Implementation Plans**: Step-by-step tasks with timelines
- **Monitoring Dashboards**: Real-time status and health metrics
- **Documentation Updates**: Automated documentation generation

### Integration Points
- **GitHub Actions**: Automated CI/CD pipeline integration
- **Pulumi Stacks**: Infrastructure change automation
- **Monitoring Systems**: Alert-driven workflow triggers
- **Documentation**: Automated updates to project documentation 