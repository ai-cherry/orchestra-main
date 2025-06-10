# Cursor AI Context Templates for Orchestra Main

## Universal Meta-Prompt
```
Context: Orchestra Main monorepo - {component}
Stack: Python 3.10 + FastAPI + React TS + Pulumi + PostgreSQL + Weaviate
Environment: Lambda Labs Cloud (single developer)
Priority: Quality > speed, stability critical
MCP: Pulumi, Sequential Thinking, GitHub, Filesystem available
Task: {specific_task}
```

## Component-Specific Templates

### Backend Development
```
Working on: {agent|api|backend_service}
Database: shared.database.UnifiedDatabase (PostgreSQL + Weaviate)
Auth: JWT with refresh rotation
Performance: <200ms responses, async patterns
Cross-impact: dashboard, mobile-app, admin-interface
```

### Frontend Development  
```
Working on: {admin-interface|dashboard}
Stack: React TS + Tailwind + React Query + Zustand
Performance: Core Web Vitals, code splitting
A11y: WCAG 2.1 AA compliance required
Cross-impact: API contracts, mobile consistency
```

### Infrastructure
```
Working on: Pulumi IaC deployment
Cloud: Lambda Labs VPS + managed services
Security: Secrets via Pulumi config only
Cost: Monitor usage, optimize for efficiency
Cross-impact: All services deployment requirements
```

## Workflow Automation
Use `@sequential-thinking` for complex multi-step tasks requiring cross-project analysis and systematic implementation planning. 