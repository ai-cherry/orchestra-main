# Orchestra AI

**Orchestra AI** is a modular, cloud-native platform for AI-driven data enrichment, workflow automation, and multi-agent orchestration.
It is designed for performance, stability, and extensibility, leveraging Docker Compose, Poetry, and GCP as first-class citizens.

---

## 🚀 Quick Start

```bash
# One-time setup (Python 3.10+, Docker Compose v2, Poetry)
docker compose build
./start.sh up

# Daily use
./start.sh shell
```

Everything else is handled by Docker and Poetry.
See [README_NO_BS.md](README_NO_BS.md) for a minimal workflow, or [UNFUCK_EVERYTHING.md](UNFUCK_EVERYTHING.md) for a full setup guide.

---

## 📖 Documentation Index

- [Project Philosophy & Priorities](PROJECT_PRIORITIES.md)
- [AI Coding Standards](docs/AI_CODING_STANDARDS.md)
- [Agent & Orchestrator Design](docs/agent_infrastructure.md)
- [Admin Interface Guide](admin-interface/README.md)
- [Automation & Deployment](docs/AUTOMATION_SUMMARY.md)
- [Troubleshooting & FAQ](docs/troubleshooting.md)
- [Full Documentation Index](docs/README.md)

---

## 🛠️ Environment & Tooling

- **Python:** 3.10+ (standardized across all services)
- **Dependency Management:** Poetry (see [pyproject.toml](pyproject.toml))
- **Containerization:** Docker Compose v2
- **Cloud:** GCP (Firestore, Secret Manager, Cloud Run)
- **Workflow Automation:** n8n, Pipedream (see docs for integration)
- **Admin Interface:** React/Node 18+ (see admin-interface/)

---

## 🗂️ Additional Notes

- All legacy and conflicting requirements files have been removed.
- Old documentation is archived in `docs/archive/old-guides/`.
- For contributing guidelines and license, see [CONTRIBUTING.md](CONTRIBUTING.md) and [LICENSE](LICENSE) (to be added).
