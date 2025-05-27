# Orchestra Documentation Index

Welcome! Start here to navigate the most relevant, up-to-date documentation for the Orchestra codebase. Each section links to a canonical guide; superseded files have been removed to keep the set concise.

## 1 — Core Overview

- [README.md](../README.md) — quick start & developer environment
- [@docs/ARCHITECTURE.md](../@docs/ARCHITECTURE.md) — system design & component diagram
- [PROJECT_PRIORITIES.md](../PROJECT_PRIORITIES.md) — performance vs. security trade-offs

## 2 — Code Quality & Testing

- [CODE_HYGIENE_README.md](../CODE_HYGIENE_README.md) — formatting, linting, CI steps
- [tests/README.md](../tests/README.md) — testing layers & LLM-mock fixtures

## 3 — Infrastructure & Deployment (Pulumi-first)

- [- [cloud_run_deployment.md](cloud_run_deployment.md)
- [infra.md](infra.md) — high-level infra topology
- **Legacy Terraform appendix:** [TERRAFORM_INFRASTRUCTURE_GUIDE.md](TERRAFORM_INFRASTRUCTURE_GUIDE.md)

## 4 — Memory System

- [memory_architecture.md](memory_architecture.md)
- [memory_system_usage_examples.md](memory_system_usage_examples.md)
- Implementation spec: [README-IMPLEMENTATION.md](../README-IMPLEMENTATION.md)

## 5 — Agents & Orchestration

- [agent_infrastructure.md](agent_infrastructure.md)
- [agent_communication_guide.md](agent_communication_guide.md)
- [MCP_SERVER_DEPLOYMENT_GUIDE.md](MCP_SERVER_DEPLOYMENT_GUIDE.md) _(optional component)_

## 6 — Security & Secrets

- [README_SECURE_CREDENTIALS.md](README_SECURE_CREDENTIALS.md)
- [SECRET_MANAGEMENT_CICD.md](SECRET_MANAGEMENT_CICD.md)
- [CREDENTIAL_IMPLEMENTATION_CHECKLIST.md](CREDENTIAL_IMPLEMENTATION_CHECKLIST.md)

## 7 — Troubleshooting & Operational Guides

- [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)
- [error_handling.md](error_handling.md)
- [rate_limit_handling.md](rate_limit_handling.md)
