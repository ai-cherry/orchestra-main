# Manual Pre-Deployment Checklist

> **NEW**: Use the automated verification script to streamline this process: `./run_pre_deployment_automated.sh`  
> The script will automate many of the steps below while still allowing for necessary manual verification.  
> See `DEPLOYMENT_AUTOMATION_README.md` for details on the automation and code duplication cleanup.

This checklist covers essential verification steps to perform after successfully running Terraform and before extensive testing.

## 1. PostgreSQL Setup

- [ ] **Run the PostgreSQL pgvector setup script:**
  ```bash
  python scripts/setup_postgres_pgvector.py --apply --schema llm
  ```
  - This configures PostgreSQL with pgvector extension and creates the necessary schema
  - Ensures vector search capabilities for the memory system are properly set up

## 2. Credentials Verification

- [ ] **Run the credentials setup script for final verification:**
  ```bash
  ./setup_credentials.sh
  ```
  - Verifies all required credentials are properly set
  - Creates/updates the .env file with the latest configuration
  - Sets up authentication for GCP, Redis, and LLM providers

## 3. System Diagnostics

- [ ] **Run comprehensive diagnostics:**
  ```bash
  python unified_diagnostics.py --all
  ```
  - Checks environment variables and basic system configuration
  - Verifies GCP authentication status
  - Tests Terraform configuration
  - Validates Phidata dependencies and integrations
  - Reviews memory manager implementation

## 4. Key Integration Tests

- [ ] **Run connection tests for Firestore/Redis:**
  ```bash
  ./run_connection_tests.sh
  ```
  - Tests connectivity to Firestore and Redis
  - Verifies authentication and configuration

- [ ] **Verify PostgreSQL connectivity:**
  ```bash
  python test_postgres_connection.py
  ```
  - Checks PostgreSQL connection configuration
  - Validates required dependencies
  - Confirms database user and permissions

- [ ] **Run LLM integration test:**
  ```bash
  python -m packages.llm.src.test_phidata_integration
  ```
  - Tests connectivity with LLM providers
  - Validates response handling

- [ ] **Run tool integration test:**
  ```bash
  python -m packages.tools.src.test_phidata_integration
  ```
  - Verifies tool functionality
  - Tests tool integration with the system

- [ ] **Run a core integration test hitting /phidata/chat endpoint:**
  ```bash
  # Choose one of these test files based on your needs:
  pytest tests/integration/phidata/test_phidata_agents_integration.py
  # or
  pytest tests/test_phidata_integration.py
  ```
  - Validates end-to-end communication
  - Tests the API endpoint and agent interactions

## 5. UI Verification

- [ ] **Verify Phidata UI loads correctly after deployment:**
  - Access the UI at the URL provided by Terraform output
    ```bash
    # If needed, get the URL with:
    terraform -chdir="infra/orchestra-terraform" output -json service_urls | jq -r '.ui'
    ```
  - Test basic interactions:
    - Send test messages
    - Check that responses are received
    - Verify tool invocations work as expected
    - Test different agent types if applicable

## Notes

- Complete these verification steps in order
- Document any failures or unexpected behavior
- If any step fails, address issues before proceeding with full testing
- For any UI verification issues, check both frontend and backend logs
