# Codebase Cleanup Analysis  
*(Repository: `orchestra-main` – 29 May 2025)*  

---

## 1 · Executive Summary
A sweep of the repository uncovered three broad problem areas:

| Area | Impact | # Findings | Priority |
|------|--------|-----------|----------|
| **Codespaces artefacts** | Confusion & wasted CI minutes | 19 refs | P1 |
| **Legacy GCP / Google-specific scripts** | Dead code, wrong infra hints | 63 refs | P1 |
| **Secret-management drift** | Potential credential leaks & duplication | 12 issues | P0 |

Cleaning these will reduce maintenance overhead, speed up CI, and align the project with the **DigitalOcean + Pulumi** deployment model and **GitHub-org secrets** policy.

---

## 2 · Codespaces References

| File | Line / Context | Recommended Action |
|------|----------------|--------------------|
| `docs/GEMINI_CODESPACES_SETUP.md` | Entire file | **Delete** (obsolete dev-environment guide) |
| `.devcontainer/**/*` | All | **Archive** to `/archive/devcontainer_legacy/` or remove; switch to Cursor doc |
| `codespaces_pip_requirements.txt` | Legacy requirements snapshot | Delete |
| `scripts/*setup_codespaces*` (none found but pattern reserved) | — | N/A |
| `core/env_config.py` | `codespaces` env var | Deprecate & remove after 2-week grace period |
| `manage_workstations.sh` | Mentions Codespaces | Trim section |
| `docs/CURSOR_AI_OPTIMIZATION_GUIDE.md` | references Codespaces vs Cursor | Update wording |
| Various `.cursor/rules/*` | Legit; keep (Cursor specific) |

**Implementation priority: P1 – sprint 1**

Steps:
1. Remove obsolete files; commit with message “chore: drop Codespaces legacy”.
2. Add migration note to `CHANGELOG.md`.
3. Strip `codespaces` field from `core/env_config.py`; add deprecation warning for two releases.

---

## 3 · Outdated GCP / Google References

| Category | Representative Files | Action |
|----------|---------------------|--------|
| Cloud Run / GCS scripts | `check_admin_ui_deployment.sh`, `MANUAL_GCP_CLEANUP_GUIDE.md`, `scripts/check_required_apis.sh` | Delete or move to `/archive/gcp_legacy/` |
| Pulumi patterns | `.cursor/rules/PULUMI_GCP_PATTERNS.mdc` | Remove (conflicts with DO stack) |
| GCP adapters | `mcp_server/adapters/jules_google_adapter.py` | **Evaluate**: if unused ⇒ delete; if used for VertexAI, move under `packages/vertex_client`. |
| Vertex AI stubs | `shared/vertex_ai/**`, `vertex_ai_refs.txt` | Keep if actively used, else archive. |
| Env vars | `core/env_config.py` (`gcp_project_id`, `gcp_service_account_key`) | Mark `deprecated=True`, schedule removal |
| CI hints | `.github/workflows/*` none critical, but ensure no `setup-gcloud` steps | Confirm & purge |
| Docs | `docs/gcp-*`, `GCP_*` plans | Move to doc archive; keep MANUAL cleanup as historical reference |

**Implementation priority: P1**

1. Create `docs/archive/` and move historical GCP docs.
2. Delete shell scripts that hard-code `gcloud`.
3. Run `pytest -q` to confirm no imports break.
4. Update Pulumi root README to clarify DigitalOcean-only.

---

## 4 · Secret-Management Inconsistencies

### 4.1 Findings
1. **Duplicate Secret Names**  
   - `OPENAI_API_KEY` vs `OPENAI_API_KEY_PROD` – diverging casing in workflow.
2. **Plaintext defaults in `core/env_config.py`** (e.g. `weaviate_api_key` default `None` but no `_secret` suffix).
3. **Scripts outputting secrets to logs**  
   - `scripts/figma_webhook_handler.js` logs full payload (ok) **but** ensure no secret included.
4. **CI secrets env block not aligned with `docs/github_org_secrets_mapping.md`**.

### 4.2 Recommendations
| Task | Owner | Priority |
|------|-------|----------|
| Introduce **`.github/secrets.yml` design doc** mapping repo → org secrets | DevOps | P0 |
| Enforce secret names via `EnvValidator` pre-commit hook (Python) | Platform | P0 |
| Replace `_PROD` overrides with **environment-specific Pulumi config** | Infra | P1 |
| Mask secret values in all custom scripts (`set -x` off, `echo $SECRET` removal) | All | P0 |
| Remove deprecated `GOOGLE_*` secrets from workflows | DevOps | P1 |

---

## 5 · Implementation Roadmap

| Sprint | Deliverables |
|--------|--------------|
| **Sprint 1 (P0/P1)** | • Remove Codespaces artefacts<br>• Migrate GCP docs to archive<br>• Finalise secret naming schema & update CI<br>• Deprecation warnings in `env_config` |
| **Sprint 2** | • Delete unused GCP/GCloud scripts & adapters<br>• Refactor workflows to single secret set<br>• Add pre-commit secret-lint |
| **Sprint 3** | • Purge deprecated env vars after grace period<br>• CI hard-fail if Codespaces/GCP refs re-introduced |
| **Sprint 4** | • Documentation refresh<br>• Tag v1.0 “DigitalOcean-first” milestone |

---

## 6 · Acceptance Criteria

1. `git grep -i codespaces` returns **0** hits (except historical archive).
2. `git grep -i gcp | wc -l` < 10, and each hit is **intentional** (VertexAI client or doc archive).
3. All secrets consumed in workflows are declared at **org level** and injected via Pulumi config – no plaintext defaults.
4. CI pipeline green; all unit & E2E tests pass.

---

## 7 · Appendix A – Full File Inventory

*Codespaces-related* (19):  
`docs/GEMINI_CODESPACES_SETUP.md` • `codespaces_pip_requirements.txt` • `.devcontainer/**/*` • `core/env_config.py` (`codespaces` var) • `manage_workstations.sh` • …

*GCP-related* (63):  
`check_admin_ui_deployment.sh` • `docs/gcp-*` • `mcp_server/scripts/gcp-*.service` • `core/env_config.py` (`gcp_*`) • `.cursor/rules/PULUMI_GCP_PATTERNS.mdc` • …

*Abridged list stored in* `audit/inventory.json`.

---

### Next Step

Open a branch **`cleanup/legacy-env`**, apply *Sprint 1* deletions, and raise a PR tagged **“⚠ BREAKING CHANGE: removes Codespaces & GCP legacy code”**.
