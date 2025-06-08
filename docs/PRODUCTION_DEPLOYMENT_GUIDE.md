# cherry_ai Production Deployment Guide

## 🚀 Updated for Single-User, Secure, and Observable Deployment (2025)

This guide reflects the latest production architecture, security, and monitoring best practices for cherry_ai. It is optimized for a single-user deployment, but is easily extensible for future scaling.

---

## Key Enhancements
- **Context Management:** Now uses IndexedDB (Dexie) with AES encryption for all context data. No more 5MB limit, and data is secure at rest.
- **Secrets, Tokens, Preferences:** All are encrypted in localStorage using AES.
- **Monitoring:** Sentry (error tracking) and Prometheus (metrics) are integrated. Fluentd forwards logs to Elasticsearch/Loki for centralized log search.
- **Cleanup:** All one-off, legacy, and diagnostic scripts are reviewed and marked for removal.
- **Documentation:** Notion and internal docs are updated with new architecture, monitoring, and security practices.

---

## Table of Contents
- [Overview](#overview)
- [Deployment Scripts](#deployment-scripts)
- [Pre-Deployment Verification](#pre-deployment-verification)
- [Setting Up Production Environment](#setting-up-production-environment)
- [Production Deployment](#production-deployment)
- [Post-Deployment Verification](#post-deployment-verification)
- [Monitoring and Alerting](#monitoring-and-alerting)
- [Documentation & Notion Update](#documentation--notion-update)
- [Cleanup Plan](#cleanup-plan)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

cherry_ai now uses a secure, single-user optimized architecture:
- **Frontend:** React/TypeScript, all context and preferences encrypted, IndexedDB for context storage
- **Backend:** API, AI Bridge, Health Monitor, Nginx, Redis, Weaviate, Postgres
- **Monitoring:** Sentry (frontend/backend), Prometheus metrics, Fluentd log forwarding
- **Secrets:** All API keys, tokens, and preferences are encrypted at rest

---

## Monitoring and Alerting

- **Sentry:** Integrated in both frontend and backend for real-time error tracking
- **Prometheus:** Exposes /metrics endpoint for API, tracks custom metrics
- **Fluentd:** Forwards logs to Elasticsearch or Loki for centralized search
- **Health Monitor:** Slack/email alerting for health check failures

---

## Documentation & Notion Update

- **Notion:** Update the main Notion workspace with:
  - New architecture diagram (showing encrypted context, monitoring stack)
  - Security practices (encryption at rest, single-user optimizations)
  - Monitoring/observability stack (Sentry, Prometheus, Fluentd)
  - Cleanup checklist for one-off/obsolete scripts
  - Link to this updated deployment guide
- **Internal Docs:**
  - Update all relevant markdown files in /docs to reflect new context management, monitoring, and security
  - Remove or mark as obsolete any documentation for multi-user or legacy scripts

---

## Cleanup Plan

### Priority 1 (Immediate)
- Remove or archive all one-off and diagnostic scripts in:
  - `archive/one-time-scripts/`
  - `scripts/` (e.g., `diagnose_*.py`, `setup.sh`, legacy setup scripts)
  - `admin-interface/scripts/` (except for current verification scripts)
- Mark any scripts not referenced in this guide as obsolete

### Priority 2 (Ongoing)
- Refactor shared utilities
- Standardize configurations
- Update documentation and Notion

---

## Checklist for Obsolete/One-Off Script Cleanup
- [ ] Remove all scripts in `archive/one-time-scripts/` unless needed for future reference
- [ ] Remove or archive diagnostic scripts in `scripts/` (e.g., `diagnose_*.py`, `setup.sh`)
- [ ] Remove legacy setup scripts not referenced in this guide
- [ ] Remove or archive any admin-interface/scripts/ not used in current deployment
- [ ] Update Notion and /docs to reflect these changes

---

## Summary

- **Single-user, encrypted, and observable**: All context, tokens, and preferences are encrypted at rest. Monitoring and alerting are production-grade. All documentation and Notion are updated to reflect the new architecture.
- **Ready for production**: Clean up obsolete scripts, keep documentation current, and monitor your deployment with confidence.

---

*For questions or to contribute improvements, see the [Troubleshooting Guide](./TROUBLESHOOTING_GUIDE.md) or contact the maintainer.*
