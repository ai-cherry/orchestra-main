# WEAVIATE-FIRST MIGRATION ROADMAP  
### Orchestra-Main · May 2025

---

## 0 · Executive Summary
We are replacing the **Dragonfly-primary memory model** with a **Weaviate-first, Postgres-steady, Redis-only-if-needed** architecture.  
The new stack runs on **two existing DigitalOcean droplets** and satisfies every current project goal:

* Dynamic, contextual memory across **Personal**, **PayReady**, **ParagonRX Clinical** domains  
* Intuitive Admin UI & Android access (voice + text)  
* Flexible MCP server mesh with standardised storage adapters  
* Large-dataset ingestion, fuzzy data intelligence, and agent orchestration

---

## 1 · Target Topology (v1.0)

| Role | Droplet | Spec | Containers/Services |
|------|---------|------|---------------------|
| Vector + Storage Node | `superagi-dev-sfo2-01` (Ubuntu 22.04) | **4 vCPU / 8 GiB / 160 GB** (resize on demand) | `weaviate:1.30` + Agents runtime |
| App / Orchestrator Node | `ubuntu-s-2vcpu-8gb-160gb-intel-sfo2-01` | **8 vCPU / 32 GiB** (resize on demand) | Postgres 16 + pgvector, Unified Python venv (SuperAGI/AutoGen & MCP), Nginx, Langfuse |
| Optional Micro-Cache | basic 1 vCPU / 1 GiB droplet | deployed only if p95 chat latency > 50 ms | Dragonfly 1.7 |

All nodes are in VPC `10.120.0.0/16` (SFO2).  
Block-storage snapshot nightly via Pulumi.

---

## 2 · Pulumi Blueprint

### 2.1 Component Graph

```
core_stack
 ├─ VectorDropletComponent        # Weaviate + volume + firewall
 ├─ AppStackComponent             # Postgres + orchestrator + Langfuse
 ├─ MicroCacheComponent (opt)     # Dragonfly
 └─ NetworkFirewallComponent      # shared inbound rules
```

### 2.2 Key Resources

| Component | New File | Purpose |
|-----------|----------|---------|
| `vector_droplet_component.py` | `infra/components/` | Provision droplet, attach 160 GB volume, install Docker, launch `weaviate.yml` with ACORN + Agents |
| `postgres_component.py` | `infra/components/` | Install Postgres 16, create `orchestrator` DB, enable pgvector |
| `resize_job.py` | `infra/components/` | Conditional droplet resize when Prometheus alert fires |
| Stack configs | `infra/Pulumi.{dev,prod}.yaml` | ORG_-prefixed secrets (`ORG_WEAVIATE_API_KEY`, `ORG_POSTGRES_PW`) |

---

## 3 · Collection & Schema Plan

| Domain | Collection/Class | Vectorizer | Key Properties |
|--------|------------------|------------|----------------|
| Personal | `Personal` | `text2vec-openai` | `owner`, `tags`, `timestamp` |
| PayReady | `PayReady` | `text2vec-openai` | `tenantId`, `unitNumber`, `status` |
| ParagonRX | `ParagonRX` | `text2vec-openai` | `trialId`, `patientId`, `phase` |
| Chat Sessions | `Session` (multi-tenant) | `text2vec-openai` | `threadId`, `speaker`, `domain` |

Limit to **4** collections to stay under Weaviate 1 000-class cap.  
Short-lived chat data is stored via **multi-tenant objects (`tenant = yyyymmdd`)** then summarised nightly.

---

## 4 · Migration Scripts (placed in `scripts/`)

### 4.1 `setup_weaviate_collections.py`
```python
"""
Creates domain classes with hybrid-search + ACORN enabled
Run once from the app node.
"""
```

### 4.2 `migrate_dragonfly_to_weaviate.py`
```python
"""
1. Connect to old Dragonfly at PAPERSCAPE_IP:6379
2. For each key `memory:*`:
      - parse JSON  ➜ MemoryItem
      - embed text with MiniLM
      - upsert into weaviate (class=Session, tenant=today)
3. Delete key after success.
Safe to run multiple times (idempotent).
"""
```

### 4.3 `copy_structured_to_postgres.py`
```python
"""
Moves ACID-worthy hash maps (billing logs, job rows) to Postgres.
Uses COPY FROM STDIN for speed.
"""
```

---

## 5 · Codebase Refactor Checklist

| Area | File / Module | Action |
|------|---------------|--------|
| Unified Memory | `shared/memory/unified_memory.py` | `use_weaviate=True, use_dragonfly=False` default; add Postgres adapter for `structured_store` |
| Weaviate Adapter | `shared/memory/weaviate_adapter.py` | Add `tenant` support + Agents batching |
| MCP Storage | `mcp_server/storage/` | Replace `redis_vector_storage.py` with thin wrapper around WeaviateAdapter |
| Env Config | `core/env_config.py` | Add `WEAVIATE_ENDPOINT`, `POSTGRES_DSN`, `ENABLE_MICRO_CACHE` |
| Admin API | `core/api/endpoints` | Change search endpoints to query Weaviate first; fall back to Postgres |
| Pulumi CI | `.github/workflows/deploy.yaml` | `pulumi up --stack=do-dev` after tests |

---

## 6 · AI-Coder Task Graph

```
T0  pull-orchestra-main
T1  implement vector_droplet_component.py
T2  implement postgres_component.py
T3  update unified_memory + adapters
T4  write migration scripts (4.1-4.3)
T5  run Pulumi preview (dev) ➜ up
T6  execute migration scripts
T7  run integration tests (/tests/integration)
T8  promote stack do-prod
T9  decommission Paperspace
```

Each task renders as a GitHub PR with unit + integration tests.  
Scripts auto-generate PR titles and labels (`infra`, `memory`, `migration`).

---

## 7 · Validation Matrix

| Probe | Target | Pass Criteria |
|-------|--------|---------------|
| `/v1/.well-known/ready` | Weaviate | HTTP 200 in < 1 s |
| `pgbench -c 16 -T 60` | Postgres | > 500 TPS |
| `curl /metrics | weaviate_query_p95_seconds` | Prometheus | < 0.15 |
| `admin-ui` NL query | end-to-end | Response in < 2 s |

---

## 8 · Rollback

1. Keep Paperspace snapshot for 7 days  
2. Retain Weaviate import CSV + Postgres dump in DO Spaces  
3. `pulumi destroy` micro-cache if added unnecessarily  
4. Re-point DNS back to Paperspace IP (15 min TTL)

---

## 9 · Timeline (8 days)

| Day | Deliverable |
|-----|-------------|
| 1 | Pulumi components & secrets setup |
| 2 | Weaviate + Postgres droplets live |
| 3 | UnifiedMemory refactor PR merged |
| 4 | Migration scripts merged |
| 5 | Data migrated, dev traffic cut-over |
| 6 | Load test, monitor, optional cache decision |
| 7 | prod DNS switch |
| 8 | documentation freeze + snapshot |

---

## 10 · References

* `services/weaviate_service.py` – current Weaviate client  
* `infra/components/weaviate_component.py` – Kubernetes version (use as pattern)  
* `docs/VECTOR_SEARCH_INTEGRATION.md` – legacy guidance  
* DigitalOcean Docs: Block Storage snapshots, Droplet resize API  
* Weaviate v1.30 Agents SDK

---

_This roadmap is intentionally explicit for autonomous AI coders.  
All scripts, Pulumi components, and env templates **MUST** reside in paths indicated above._  
