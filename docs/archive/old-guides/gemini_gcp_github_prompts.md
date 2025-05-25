# Gemini Prompts for GCP & GitHub Integration

This document provides a collection of effective prompts to use with Gemini when working with Google Cloud Platform (GCP) and GitHub integration. These prompts are designed to help you get the most out of Gemini for various tasks related to infrastructure management, CI/CD, and AI services.

## Infrastructure Setup Prompts

### Terraform Configuration

```
Help me create a Terraform configuration for setting up the following GCP resources for my project 'cherry-ai-project':
- A Cloud Run service for hosting a FastAPI application
- A Cloud SQL PostgreSQL instance
- A Vertex AI endpoint for model serving
- A service account with appropriate permissions
- Secret Manager secrets for storing sensitive information

Include best practices for security and cost optimization.
```

### IAM Permissions

```
I need to create a service account for my AI application that will use Vertex AI and Gemini APIs. What are the minimum IAM permissions required? Please provide the specific roles and explain why each is needed.
```

### Workload Identity Federation

```
Explain how to set up Workload Identity Federation between GitHub Actions and GCP for my project 'cherry-ai-project'. Include the Terraform configuration and the GitHub Actions workflow configuration.
```

## CI/CD Prompts

### GitHub Actions Workflow

```
Create a GitHub Actions workflow for my Python FastAPI application that:
1. Runs tests
2. Builds a Docker image
3. Pushes the image to Artifact Registry
4. Deploys to Cloud Run
5. Uses Workload Identity Federation for authentication

The project is using Poetry for dependency management.
```

### Secret Management

```
What's the best way to manage secrets between GitHub and GCP for my CI/CD pipeline? I need to store API keys, database credentials, and service account keys securely while making them available to my GitHub Actions workflows and Cloud Run services.
```

### Deployment Strategies

```
Explain different deployment strategies (blue-green, canary, etc.) for Cloud Run services using GitHub Actions. Provide examples of how to implement each strategy.
```

## AI Services Prompts

### Vertex AI Integration

```
Show me how to integrate Vertex AI with my FastAPI application. I need to:
1. Authenticate with a service account
2. Send requests to a deployed model
3. Process the responses
4. Handle errors and retries

Provide Python code examples using the google-cloud-aiplatform library.
```

### Gemini API Usage

```
Provide Python code examples for using the Gemini API with a service account. Include examples for:
1. Text generation
2. Multi-turn conversations
3. Image understanding
4. Code generation

Use the google.generativeai library.
```

### Model Deployment

```
Walk me through the process of deploying a custom PyTorch model to Vertex AI. Include:
1. Model packaging
2. Container configuration
3. Deployment options
4. Scaling and monitoring

Provide both CLI commands and Python code examples.
```

## Troubleshooting Prompts

### Authentication Issues

```
I'm getting a "Permission denied" error when my GitHub Actions workflow tries to access GCP resources using Workload Identity Federation. Here's my workflow configuration and error message:

[Insert your workflow configuration and error message]

What could be causing this issue and how can I fix it?
```

### Deployment Failures

```
My Cloud Run deployment is failing with the following error:

[Insert error message]

Here's my deployment configuration:

[Insert deployment configuration]

What might be causing this issue and how can I resolve it?
```

### Performance Optimization

```
My Vertex AI endpoint is experiencing high latency. The model is a transformer-based text classification model with the following configuration:

[Insert model configuration]

What are some strategies to improve performance without significantly increasing costs?
```

## Infrastructure as Code Prompts

### Terraform Modules

```
Help me create a reusable Terraform module for setting up a complete AI infrastructure on GCP, including:
1. Vertex AI resources
2. Cloud Storage buckets
3. Cloud Run services
4. IAM permissions
5. Secret Manager secrets

The module should be parameterized and follow best practices for modularity and reusability.
```

### CI/CD Pipeline as Code

```
Create a complete CI/CD pipeline as code for my AI application, including:
1. GitHub Actions workflows
2. Terraform configurations
3. Deployment scripts
4. Testing configurations

The pipeline should support multiple environments (dev, staging, prod) and include safeguards to prevent accidental deployments to production.
```

## Security Prompts

### Security Best Practices

```
What are the security best practices for a GCP project that uses Vertex AI and Gemini APIs? Include recommendations for:
1. IAM permissions
2. Network security
3. Secret management
4. Data protection
5. Compliance considerations
```

### Security Scanning

```
How can I implement security scanning in my GitHub Actions workflow to identify vulnerabilities in my Python application before deploying to Cloud Run? Include specific tools and configuration examples.
```

## Cost Optimization Prompts

### Cost Analysis

```
Help me analyze and optimize the costs of my GCP infrastructure for AI workloads. I'm currently using:
1. Vertex AI for model training and serving
2. Cloud Run for API hosting
3. Cloud Storage for data storage
4. Cloud SQL for metadata

What are some strategies to reduce costs without sacrificing performance?
```

### Resource Sizing

```
What's the optimal resource configuration for my Cloud Run service that hosts a FastAPI application serving Vertex AI models? The application receives approximately 100 requests per minute with occasional spikes up to 500 requests per minute.
```

## Monitoring and Logging Prompts

### Monitoring Setup

```
Help me set up comprehensive monitoring for my AI application on GCP. I need to monitor:
1. Cloud Run service health and performance
2. Vertex AI endpoint performance and prediction quality
3. API latency and error rates
4. Cost and resource utilization

Include specific metrics to track and alerting thresholds.
```

### Log Analysis

```
I'm seeing occasional errors in my Cloud Run service logs. Here's a sample of the error messages:

[Insert log samples]

What might be causing these errors and how can I set up better logging to diagnose the issue?
```

## Tips for Effective Prompting

1. **Be Specific**: Include project names, resource types, and specific requirements in your prompts.
2. **Provide Context**: Include relevant information about your current setup and constraints.
3. **Ask for Explanations**: Request explanations along with code or configurations to better understand the solutions.
4. **Iterate**: If the initial response doesn't fully address your needs, refine your prompt and ask follow-up questions.
5. **Share Error Messages**: When troubleshooting, share the exact error messages and relevant configurations.

## Example Conversation Flow

Here's an example of how to have an effective conversation with Gemini about GCP and GitHub integration:

**User**:

```
I need to set up a CI/CD pipeline for my AI application that uses Vertex AI. The application is a FastAPI service that calls Vertex AI endpoints for predictions. I want to use GitHub Actions for CI/CD and deploy to Cloud Run. What's the best way to structure this?
```

**Gemini**:
[Provides initial recommendations]

**User**:

```
That's helpful. Now I need to set up authentication between GitHub Actions and GCP. I've heard about Workload Identity Federation but I'm not sure how to implement it. Can you provide specific steps and configurations?
```

**Gemini**:
[Provides detailed instructions for Workload Identity Federation]

**User**:

```
I'm getting this error when trying to set up Workload Identity Federation: [error message]. What might be causing this?
```

**Gemini**:
[Provides troubleshooting advice]

This iterative approach helps you get more detailed and relevant information from Gemini.
