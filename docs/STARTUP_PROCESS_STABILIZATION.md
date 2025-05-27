# AI Orchestra Stabilization Plan

This document outlines the steps taken and recommendations for stabilizing the AI Orchestra project's development environment, CI/CD pipeline, and infrastructure.

## 1. DevContainer Environment Improvements

### Completed Changes

- **Enhanced Setup Script**: Updated `.devcontainer/setup.sh` with:
  - Improved error handling and colored output
  - Poetry version consistency checks
  - Automatic lock file regeneration when needed
  - Better dependency installation with retry mechanism

### Additional Recommendations

- **Update Base Image**: Consider using a more specific Python image version in `.devcontainer/devcontainer.json`:

  ```json
  "image": "mcr.microsoft.com/devcontainers/python:3.10-bullseye",
  ```

- **Add Development Tools**: Add development tools to the DevContainer for better debugging:

  ```json
  "features": {
    "ghcr.io/devcontainers/features/terraform:1": {
      "version": "1.11.3"
    },
    "ghcr.io/devcontainers/features/docker-outside-of-docker:1": {},
    "ghcr.io/devcontainers/features/google-cloud-cli:1": {
      "version": "latest",
      "install_components": "gke-gcloud-auth-plugin,beta"
    },
    "ghcr.io/devcontainers/features/github-cli:1": {},
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.11"
    }
  }
  ```

- **Add VS Code Extensions**: Add more VS Code extensions for better development experience:
  ```json
  "extensions": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "hashicorp.terraform",
    "ms-azuretools.vscode-docker",
    "googlecloudtools.cloudcode",
    "github.copilot",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "redhat.vscode-yaml",
    "eamodio.gitlens",
    "streetsidesoftware.code-spell-checker"
  ]
  ```

## 2. CI/CD Pipeline Improvements

### Completed Changes

- **Added Validation Job**: Added a new job to validate configuration before running tests:

  - Checks Poetry lock file consistency
  - Validates Terraform configuration

- **Updated GitHub Actions**: Updated all GitHub Actions to latest versions:

  - actions/checkout@v4
  - actions/setup-python@v5
  - actions/cache@v4
  - docker/build-push-action@v5
  - google-github-actions/deploy-cloudrun@v2

- **Added Retry Mechanism**: Added retry mechanism for Poetry dependency installation

- **Added Deployment Verification**: Added a step to verify deployment success

### Additional Recommendations

- **Add Terraform Plan Job**: Add a job to run `terraform plan` and comment the plan on PRs:

  ```yaml
  terraform-plan:
    name: Terraform Plan
    runs-on: ubuntu-latest
    needs: validate
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.11.3

      - name: Authenticate to         uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER_ID }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}
          token_format: access_token

      - name: Terraform Init
        run: |
          cd terraform
          terraform init

      - name: Terraform Plan
        id: plan
        run: |
          cd terraform
          terraform plan -no-color -out=tfplan

      - name: Comment Plan
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            const output = `#### Terraform Plan 📝
            \`\`\`
            ${{ steps.plan.outputs.stdout }}
            \`\`\`
            `;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            })
  ```

- **Add Security Scanning**: Add security scanning for Docker images and dependencies:

  ```yaml
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: validate
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: |
          pip install safety bandit

      - name: Run safety check
        run: |
          safety check -r requirements.txt

      - name: Run bandit
        run: |
          bandit -r . -x tests/
  ```

## 3.
### Completed Changes

- **Updated ### Additional Recommendations

- **Use Terraform for API Enablement**: Move API enablement to Terraform:

  ```hcl
  # terraform/apis.tf
  resource "google_project_service" "required_apis" {
    for_each = toset([
      "cloudresourcemanager.googleapis.com",
      "compute.googleapis.com",
      "containerregistry.googleapis.com",
      "artifactregistry.googleapis.com",
      "run.googleapis.com",
      "secretmanager.googleapis.com",
      "aiplatform.googleapis.com",
      "MongoDB
      "redis.googleapis.com",
      "cloudbuild.googleapis.com",
      "iam.googleapis.com",
      "cloudtasks.googleapis.com",
      "pubsub.googleapis.com",
      "vpcaccess.googleapis.com",
      "iamcredentials.googleapis.com",
      "sts.googleapis.com"
    ])

    project = var.project_id
    service = each.key

    disable_dependent_services = false
    disable_on_destroy         = false
  }
  ```

- **Use Terraform for Workload Identity Federation**: Move Workload Identity Federation setup to Terraform:

  ```hcl
  # terraform/github-wif.tf
  resource "google_iam_workload_identity_pool" "github_pool" {
    workload_identity_pool_id = "github-actions-pool"
    display_name              = "GitHub Actions Pool"
    description               = "Identity pool for GitHub Actions"
  }

  resource "google_iam_workload_identity_pool_provider" "github_provider" {
    workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
    workload_identity_pool_provider_id = "github-provider"
    display_name                       = "GitHub Provider"

    attribute_mapping = {
      "google.subject"       = "assertion.sub"
      "attribute.actor"      = "assertion.actor"
      "attribute.repository" = "assertion.repository"
    }

    oidc {
      issuer_uri = "https://token.actions.githubusercontent.com"
    }
  }

  resource "google_service_account" "github_actions" {
    account_id   = "github-actions-wif"
    display_name = "GitHub Actions WIF Service Account"
    description  = "Service account for GitHub Actions using Workload Identity Federation"
  }

  resource "google_service_account_iam_binding" "workload_identity_binding" {
    service_account_id = google_service_account.github_actions.name
    role               = "roles/iam.workloadIdentityUser"

    members = [
      "principalSet://iam.googleapis.com/projects/${var.project_number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github_pool.workload_identity_pool_id}/attribute.repository/${var.github_repo_owner}/${var.github_repo_name}"
    ]
  }

  resource "google_project_iam_member" "service_account_roles" {
    for_each = toset([
      "roles/run.admin",
      "roles/artifactregistry.admin",
      "roles/storage.admin",
      "roles/secretmanager.admin",
      "roles/iam.serviceAccountUser"
    ])

    project = var.project_id
    role    = each.key
    member  = "serviceAccount:${google_service_account.github_actions.email}"
  }
  ```

## 4. Memory Architecture Recommendations

For the multi-agent system with hyper-contextualized memory, we recommend a layered approach:

### Short-term Memory (Redis)

- Use Redis for fast, ephemeral storage of conversation context
- Store recent messages, agent states, and temporary data
- Configure with appropriate TTL for automatic cleanup

```python
# Example Redis memory implementation
class RedisShortTermMemory:
    def __init__(self, redis_client, ttl=3600):
        self.redis = redis_client
        self.ttl = ttl

    async def store(self, key, value, namespace="conversation"):
        full_key = f"{namespace}:{key}"
        await self.redis.set(full_key, json.dumps(value), ex=self.ttl)

    async def retrieve(self, key, namespace="conversation"):
        full_key = f"{namespace}:{key}"
        data = await self.redis.get(full_key)
        return json.loads(data) if data else None
```

### Mid-term Memory (MongoDB

- Use MongoDB
- Store conversation summaries, agent knowledge, and user preferences
- Organize by collections for different data types

```python
# Example MongoDB
class MongoDB
    def __init__(self, MongoDB
        self.db = MongoDB

    async def store(self, collection, document_id, data):
        doc_ref = self.db.collection(collection).document(document_id)
        await doc_ref.set(data, merge=True)

    async def retrieve(self, collection, document_id):
        doc_ref = self.db.collection(collection).document(document_id)
        doc = await doc_ref.get()
        return doc.to_dict() if doc.exists else None
```

### Long-term Memory (Vector Search)

- Use - Store embeddings of important information for retrieval by similarity
- Index by conversation, topic, or agent

```python
# Example Vector Search memory implementation
class VectorLongTermMemory:
    def __init__(self, embedding_service, vector_search_client):
        self.embedding_service = embedding_service
        self.vector_search = vector_search_client

    async def store(self, text, metadata=None):
        embedding = await self.embedding_service.embed_text(text)
        await self.vector_search.upsert(embedding, metadata)

    async def search(self, query, limit=5):
        query_embedding = await self.embedding_service.embed_text(query)
        results = await self.vector_search.search(query_embedding, limit=limit)
        return results
```

### Memory Manager

- Create a unified memory manager that orchestrates all memory types
- Implement automatic promotion/demotion between memory layers
- Add context-aware retrieval strategies

```python
# Example Memory Manager
class LayeredMemoryManager:
    def __init__(self, short_term, mid_term, long_term):
        self.short_term = short_term
        self.mid_term = mid_term
        self.long_term = long_term

    async def store(self, data, importance="low"):
        # Store in appropriate layers based on importance
        await self.short_term.store(data["id"], data)

        if importance in ["medium", "high"]:
            await self.mid_term.store("memories", data["id"], data)

        if importance == "high":
            await self.long_term.store(data["content"], metadata=data)

    async def retrieve_context(self, query, conversation_id):
        # Get context from all memory layers
        context = {
            "recent": await self.short_term.retrieve(conversation_id),
            "related": await self.mid_term.retrieve("memories", conversation_id),
            "semantic": await self.long_term.search(query)
        }
        return context
```

## 5. Next Steps

1. **Complete Poetry Lock**: Wait for the Poetry lock command to complete and verify the lock file is updated correctly.

2. **Test DevContainer**: Rebuild the DevContainer to test the improved setup script.

3. **Test CI/CD Pipeline**: Push a small change to trigger the CI/CD pipeline and verify it works correctly.

4. **Implement Memory Architecture**: Start implementing the layered memory architecture using the recommended approach.

5. **Move to Terraform**: Gradually move manual
