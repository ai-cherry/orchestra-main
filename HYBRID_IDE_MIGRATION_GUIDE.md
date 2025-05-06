# AGI Baby Cherry Project - Hybrid IDE Migration Guide

This guide outlines the implementation of the optimized hybrid IDE setup and migration plan for the AGI Baby Cherry project, with a focus on performance and reliability.

## Table of Contents

1. [Overview](#overview)
2. [Hybrid IDE Configuration](#hybrid-ide-configuration)
3. [Pre-Migration Validation Tools](#pre-migration-validation-tools)
4. [Monitoring Setup](#monitoring-setup)
5. [Implementation Steps](#implementation-steps)
6. [Post-Migration Optimization](#post-migration-optimization)

## Overview

This migration plan implements an optimized hybrid IDE environment with enhanced performance, testing capabilities, and monitoring. The key components are:

- **Optimized Cloud Workstation Configuration**: Enhanced compute resources with AMD Milan processors
- **IDE Stress Testing**: Validation scripts to ensure IDE stability under load
- **Monitoring Stack**: Dashboards and alerts for system performance
- **Gemini Code Assist Integration**: AI-powered development tools

## Hybrid IDE Configuration

The hybrid IDE configuration has been optimized with the following specifications:

- **Machine Type**: n2d-standard-32 (AMD Milan optimized)
- **GPU**: 2x NVIDIA Tesla T4
- **Boot Disk**: 500GB SSD
- **Persistent Storage**: 1TB SSD mounted at `/home/agent/mounted_bucket`
- **Container Image**: us-docker.pkg.dev/cloud-workstations-images/predefined/intellij-ultimate:latest
- **Environment Variables**: Configured for Gemini API, Vertex AI, and Redis connections

Implementation file: `infra/cloud_workstation_config.tf`

### Key Features

- **Enhanced Performance**: The n2d-standard-32 machine type provides 32 vCPUs with AMD Milan processors, offering better price/performance than the previous e2-standard-8 configuration
- **Increased GPU Capacity**: Doubled the GPU capacity with 2x NVIDIA Tesla T4 GPUs to support more intensive AI workloads
- **Secure Networking**: Configured with private networking and shielded VM features
- **Persistent Storage**: Added a dedicated 1TB SSD for agent memory persistence
- **Development Environment**: Pre-configured with IntelliJ Ultimate and JupyterLab

## Pre-Migration Validation Tools

### IDE Stress Test

A comprehensive stress testing tool has been created to validate the stability and performance of the Cloud Workstation environment under load.

Implementation files:
- `agent/tests/ide_stress_test.py`: Main stress test script
- `scripts/run_ide_stress_test.sh`: Helper script to execute the stress test

#### Testing Capabilities

The stress test simulates developer activities with configurable parameters:
- **Threading**: Default 32 concurrent threads to simulate multiple operations
- **Duration**: Configurable test duration (default: 1 hour)
- **Operations**: File operations, Git commands, build processes, search, code formatting

#### Performance Metrics

The test collects and reports the following metrics:
- CPU utilization
- Memory usage
- Disk I/O
- Network I/O
- Thread count

#### Usage

```bash
# Run the stress test with default settings
./scripts/run_ide_stress_test.sh

# Run with custom parameters
python3 agent/tests/ide_stress_test.py --threads=64 --duration=7200
```

### Gemini Code Assist Configuration

A configuration file for Gemini Code Assist has been created to enable AI-powered development:

Implementation file: `.gemini-code-assist.yaml`

#### Features

- **Project Context**: Configured to index workspace directories with priority settings
- **Tool Integrations**: Set up for Vertex AI, Redis, and AlloyDB
- **Custom Commands**: Defined code assist commands for query optimization, Cloud Run deployment, and documentation
- **Model Configuration**: Set to use Gemini 2.5 with appropriate parameters

## Monitoring Setup

A comprehensive monitoring configuration has been implemented to track system performance and health.

Implementation file: `infra/monitoring_config.tf`

### Monitoring Features

- **Alert Policies**: Configured for Redis-AlloyDB sync latency, CPU usage, memory usage, and connection errors
- **Custom Dashboards**: Created for sync performance and IDE stress test results
- **Performance Metrics**: Set P99 latency target of <5ms for Redis-AlloyDB sync

### Metrics Upload Tool

A script has been created to upload IDE stress test metrics to Cloud Monitoring:

Implementation file: `scripts/upload_stress_test_metrics.py`

#### Usage

```bash
# Upload metrics to Cloud Monitoring
./scripts/upload_stress_test_metrics.py --input=/path/to/ide_stress_metrics.json \
  --machine-type=n2d-standard-32 \
  --workstation-id=hybrid-workstation-1
```

## Implementation Steps

Follow these steps to implement the migration:

1. **Update Cloud Workstation Configuration**

   ```bash
   # Navigate to the project directory
   cd /workspaces/orchestra-main

   # Apply Terraform configuration
   terraform init
   terraform plan -target=google_workstations_workstation_config.hybrid_config
   terraform apply -target=google_workstations_workstation_config.hybrid_config
   ```

2. **Set Up Monitoring**

   ```bash
   # Apply monitoring configuration
   terraform plan -target=module.monitoring
   terraform apply -target=module.monitoring
   ```

3. **Run Pre-Migration Validation**

   ```bash
   # Copy files to the Cloud Workstation
   gcloud workstations ssh hybrid-ide --command="mkdir -p /home/user/agent/tests /home/user/scripts"
   gcloud workstations scp agent/tests/ide_stress_test.py hybrid-ide:/home/user/agent/tests/
   gcloud workstations scp scripts/run_ide_stress_test.sh hybrid-ide:/home/user/scripts/

   # Run stress test on the workstation
   gcloud workstations ssh hybrid-ide --command="bash /home/user/scripts/run_ide_stress_test.sh"
   ```

4. **Set Up Gemini Code Assist**

   ```bash
   # Copy Gemini Code Assist configuration
   gcloud workstations ssh hybrid-ide --command="mkdir -p /home/user"
   gcloud workstations scp .gemini-code-assist.yaml hybrid-ide:/home/user/
   ```

5. **Validate Redis-AlloyDB Sync**

   ```bash
   # Check sync latency
   gcloud monitoring metrics list --filter="custom.googleapis.com/sync_latency"
   
   # View sync performance dashboard
   echo "Visit: https://console.cloud.google.com/monitoring/dashboards/custom/redis-alloydb-sync"
   ```

## Post-Migration Optimization

After initial deployment, optimize the environment with these steps:

1. **AlloyDB Tuning**
   - Enable columnar engine for analytics
   - Implement vector indexes for high-dimensional data
   - Fine-tune connection pooling

2. **Redis Optimization**
   - Configure tiered storage with RAM/SSD layers
   - Adjust eviction policies for memory management
   - Optimize cache expiration timeouts

3. **AI Workflow Enhancements**
   - Fine-tune Gemini Code Assist parameters
   - Add custom code completion prompts
   - Configure auto-documentation generation

---

## References

- [Google Cloud Workstations Documentation](https://cloud.google.com/workstations/docs)
- [AlloyDB Vector Search Documentation](https://cloud.google.com/alloydb/docs/vector-search)
- [Gemini Code Assist Reference](https://cloud.google.com/vertex-ai/docs/generative-ai/code-assist)
- [Cloud Monitoring Dashboard Reference](https://cloud.google.com/monitoring/dashboards)
