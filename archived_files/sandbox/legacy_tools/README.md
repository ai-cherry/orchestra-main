# Deprecated Tools

This directory contains deprecated tools that have been superseded by more standard approaches.

## Vertex AI Agent Manager

**Status: Deprecated – superseded by direct Terraform workflows**

### Original Intent

The Vertex AI Agent Manager was an attempt to create an automation layer for infrastructure operations using Google Cloud's Vertex AI services. It aimed to provide:

- A unified interface (CLI and API) for infrastructure operations
- Automated agent team creation
- Vector embeddings management
- Game session handling
- Resource monitoring

### Reasons for Deprecation

The implementation had several limitations:

1. **Limited Integration**: Despite the name, it didn't actually use Vertex AI capabilities beyond basic initialization.
2. **Complexity**: Added an unnecessary abstraction layer that obscured Terraform's native output.
3. **Error Handling**: Used `os.system` calls with minimal error handling.
4. **Misleading Branding**: The "AI" aspect was mostly aspirational, with many features mocked rather than implemented.
5. **Low Resilience**: Any non-zero exit code from a subprocess would fail the entire operation.

### Replacement Approach

This has been replaced with a more straightforward Infrastructure as Code (IaC) approach:

```bash
cd infra/dev  # or prod
terraform init
terraform apply -var="env=dev"
```

See `docs/infra.md` for complete infrastructure documentation.
