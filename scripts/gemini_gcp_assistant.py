#!/usr/bin/env python3
"""
Gemini GCP Assistant - A script to interact with Gemini Cloud for GCP setup and testing.

This script provides a command-line interface to interact with Gemini Cloud
for various GCP infrastructure management tasks, including:
- Generating Terraform configurations
- Analyzing and optimizing GCP resources
- Creating and testing deployment scripts
- Troubleshooting GCP issues

Usage:
    python gemini_gcp_assistant.py --task <task_name> [--input <input_file>] [--output <output_file>]

Example:
    python gemini_gcp_assistant.py --task generate_terraform --output terraform/main.tf
"""

import argparse
import json
import os
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    print("Google Generative AI SDK not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai"])
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Configuration
DEFAULT_MODEL = "gemini-1.5-pro"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.95
DEFAULT_TOP_K = 40
DEFAULT_MAX_OUTPUT_TOKENS = 8192

# Task-specific prompts
TASK_PROMPTS = {
    "generate_terraform": """
    You are a GCP infrastructure expert. Create a Terraform configuration for the following GCP resources:
    - A Cloud Run service for the AI Orchestra API
    - A Cloud Run service for the AI Orchestra UI
    - A Firestore database
    - A Secret Manager for storing API keys
    - A service account with appropriate permissions
    - Workload Identity Federation for GitHub Actions

    Use the following variables:
    - project_id: {project_id}
    - region: {region}
    - environment: {environment}

    Follow these best practices:
    - Use modules for reusable components
    - Use variables for configurable values
    - Use locals for computed values
    - Use outputs for important information
    - Use data sources for existing resources
    - Use providers for GCP authentication
    - Use terraform backend for state management

    The configuration should be production-ready, secure, and follow GCP best practices.
    """,
    
    "analyze_resources": """
    You are a GCP cost optimization expert. Analyze the following GCP resources and provide recommendations for cost optimization:
    
    {resource_data}
    
    Consider the following:
    - Rightsizing resources
    - Using committed use discounts
    - Using preemptible VMs
    - Using spot VMs
    - Using custom machine types
    - Using regional resources
    - Using lifecycle policies
    - Using autoscaling
    
    Provide specific recommendations with estimated cost savings.
    """,
    
    "create_deployment_script": """
    You are a GCP deployment expert. Create a deployment script for the AI Orchestra application with the following requirements:
    
    - Deploy to Cloud Run
    - Use Terraform for infrastructure
    - Use GitHub Actions for CI/CD
    - Use Workload Identity Federation for authentication
    - Use Secret Manager for secrets
    - Use Container Registry for container images
    
    The script should handle the following:
    - Building the container image
    - Pushing the image to Container Registry
    - Applying Terraform configuration
    - Updating Cloud Run service
    - Verifying deployment
    - Rolling back on failure
    
    Use the following variables:
    - project_id: {project_id}
    - region: {region}
    - environment: {environment}
    
    The script should be production-ready, secure, and follow GCP best practices.
    """,
    
    "troubleshoot_issue": """
    You are a GCP troubleshooting expert. Analyze the following error and provide a solution:
    
    {error_message}
    
    Consider the following:
    - Common GCP service issues
    - IAM permissions
    - Network configuration
    - Resource limits
    - API enablement
    - Service dependencies
    
    Provide a step-by-step solution with commands to fix the issue.
    """,
    
    "optimize_terraform": """
    You are a Terraform optimization expert. Analyze the following Terraform configuration and provide recommendations for improvement:
    
    {terraform_config}
    
    Consider the following:
    - Code organization
    - Variable usage
    - Resource naming
    - Resource dependencies
    - Module usage
    - Provider configuration
    - Backend configuration
    - Security best practices
    - Performance optimization
    
    Provide specific recommendations with code examples.
    """,
    
    "generate_test_script": """
    You are a GCP testing expert. Create a test script for the following GCP resources:
    
    {resource_data}
    
    The test script should:
    - Verify resource creation
    - Verify resource configuration
    - Verify resource connectivity
    - Verify resource performance
    - Verify resource security
    
    Use the following tools:
    - gcloud CLI
    - curl
    - jq
    - Python (if needed)
    
    The script should be production-ready, secure, and follow GCP best practices.
    """,
    
    "setup_monitoring": """
    You are a GCP monitoring expert. Create a monitoring configuration for the AI Orchestra application with the following requirements:
    
    - Monitor Cloud Run services
    - Monitor Firestore database
    - Monitor API latency
    - Monitor error rates
    - Monitor resource utilization
    
    Use the following:
    - Cloud Monitoring
    - Cloud Logging
    - Custom metrics
    - Alerting policies
    - Dashboards
    
    The configuration should be production-ready, secure, and follow GCP best practices.
    """,
    
    "create_backup_script": """
    You are a GCP backup expert. Create a backup script for the AI Orchestra application with the following requirements:
    
    - Backup Firestore database
    - Backup Cloud Storage buckets
    - Backup configuration files
    - Schedule regular backups
    - Implement retention policies
    
    Use the following:
    - gcloud CLI
    - Cloud Scheduler
    - Cloud Functions
    - Cloud Storage
    
    The script should be production-ready, secure, and follow GCP best practices.
    """,
    
    "setup_ci_cd": """
    You are a CI/CD expert. Create a GitHub Actions workflow for the AI Orchestra application with the following requirements:
    
    - Build and test on pull requests
    - Deploy to dev environment on merge to develop branch
    - Deploy to staging environment on merge to staging branch
    - Deploy to production environment on merge to main branch
    - Use Workload Identity Federation for authentication
    - Use Secret Manager for secrets
    
    The workflow should:
    - Run linting and tests
    - Build container images
    - Push images to Container Registry
    - Apply Terraform configuration
    - Update Cloud Run services
    - Verify deployment
    - Notify on success or failure
    
    The workflow should be production-ready, secure, and follow GitHub Actions best practices.
    """,
}

class GeminiGCPAssistant:
    """A class to interact with Gemini Cloud for GCP infrastructure management."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Gemini GCP Assistant.
        
        Args:
            api_key: The Gemini API key. If not provided, it will be read from the
                GEMINI_API_KEY environment variable or from the gemini.key file.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        
        if not self.api_key:
            # Try to read from gemini.key file
            key_file = Path("gemini.key")
            if key_file.exists():
                self.api_key = key_file.read_text().strip()
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Please provide it as an argument, "
                "set the GEMINI_API_KEY environment variable, or create a gemini.key file."
            )
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Get available models
        self.models = [m.name for m in genai.list_models() if "gemini" in m.name.lower()]
        
        if not self.models:
            raise ValueError("No Gemini models found. Please check your API key.")
        
        # Use the default model if available, otherwise use the first available model
        self.model_name = DEFAULT_MODEL if DEFAULT_MODEL in self.models else self.models[0]
        
        # Create the model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": DEFAULT_TEMPERATURE,
                "top_p": DEFAULT_TOP_P,
                "top_k": DEFAULT_TOP_K,
                "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
    
    def get_gcp_project_info(self) -> Dict[str, str]:
        """Get information about the current GCP project.
        
        Returns:
            A dictionary containing information about the current GCP project.
        """
        try:
            # Get the project ID
            import subprocess
            project_id = subprocess.check_output(
                ["gcloud", "config", "get-value", "project"], 
                universal_newlines=True
            ).strip()
            
            # Get the project number
            project_number = subprocess.check_output(
                ["gcloud", "projects", "describe", project_id, "--format=value(projectNumber)"],
                universal_newlines=True
            ).strip()
            
            # Get the default region
            region = subprocess.check_output(
                ["gcloud", "config", "get-value", "compute/region"],
                universal_newlines=True
            ).strip()
            
            # Get the default zone
            zone = subprocess.check_output(
                ["gcloud", "config", "get-value", "compute/zone"],
                universal_newlines=True
            ).strip()
            
            return {
                "project_id": project_id,
                "project_number": project_number,
                "region": region,
                "zone": zone,
                "environment": "dev",  # Default to dev environment
            }
        except Exception as e:
            print(f"Error getting GCP project info: {e}")
            return {
                "project_id": "cherry-ai-project",
                "project_number": "123456789012",
                "region": "us-central1",
                "zone": "us-central1-a",
                "environment": "dev",
            }
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a response from Gemini Cloud.
        
        Args:
            prompt: The prompt to send to Gemini Cloud.
            **kwargs: Additional parameters to format the prompt.
        
        Returns:
            The generated response.
        """
        # Format the prompt with the provided parameters
        formatted_prompt = textwrap.dedent(prompt).format(**kwargs)
        
        # Generate the response
        response = self.model.generate_content(formatted_prompt)
        
        # Return the response text
        return response.text
    
    def execute_task(self, task: str, input_file: Optional[str] = None, **kwargs) -> str:
        """Execute a task using Gemini Cloud.
        
        Args:
            task: The task to execute.
            input_file: The input file to read data from.
            **kwargs: Additional parameters to format the prompt.
        
        Returns:
            The generated response.
        """
        if task not in TASK_PROMPTS:
            raise ValueError(f"Unknown task: {task}. Available tasks: {', '.join(TASK_PROMPTS.keys())}")
        
        # Get the prompt for the task
        prompt = TASK_PROMPTS[task]
        
        # If an input file is provided, read its contents
        if input_file:
            with open(input_file, "r") as f:
                file_content = f.read()
            
            # Add the file content to the kwargs
            if task == "analyze_resources" or task == "generate_test_script":
                kwargs["resource_data"] = file_content
            elif task == "troubleshoot_issue":
                kwargs["error_message"] = file_content
            elif task == "optimize_terraform":
                kwargs["terraform_config"] = file_content
        
        # Get GCP project info if not provided
        project_info = self.get_gcp_project_info()
        for key, value in project_info.items():
            if key not in kwargs:
                kwargs[key] = value
        
        # Generate the response
        return self.generate_response(prompt, **kwargs)

def main():
    """Main function to parse arguments and execute tasks."""
    parser = argparse.ArgumentParser(description="Gemini GCP Assistant")
    parser.add_argument("--task", required=True, choices=TASK_PROMPTS.keys(),
                        help="The task to execute")
    parser.add_argument("--input", help="The input file to read data from")
    parser.add_argument("--output", help="The output file to write the response to")
    parser.add_argument("--api-key", help="The Gemini API key")
    parser.add_argument("--model", help="The Gemini model to use")
    parser.add_argument("--temperature", type=float, help="The temperature for generation")
    parser.add_argument("--project-id", help="The GCP project ID")
    parser.add_argument("--region", help="The GCP region")
    parser.add_argument("--environment", help="The deployment environment (dev, staging, prod)")
    
    args = parser.parse_args()
    
    try:
        # Create the assistant
        assistant = GeminiGCPAssistant(api_key=args.api_key)
        
        # Override the model if provided
        if args.model:
            if args.model in assistant.models:
                assistant.model_name = args.model
                assistant.model = genai.GenerativeModel(
                    model_name=assistant.model_name,
                    generation_config={
                        "temperature": args.temperature or DEFAULT_TEMPERATURE,
                        "top_p": DEFAULT_TOP_P,
                        "top_k": DEFAULT_TOP_K,
                        "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
                    },
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
            else:
                print(f"Warning: Model {args.model} not found. Using {assistant.model_name} instead.")
        
        # Prepare kwargs for the task
        kwargs = {}
        if args.project_id:
            kwargs["project_id"] = args.project_id
        if args.region:
            kwargs["region"] = args.region
        if args.environment:
            kwargs["environment"] = args.environment
        
        # Execute the task
        response = assistant.execute_task(args.task, args.input, **kwargs)
        
        # Write the response to the output file or print it
        if args.output:
            with open(args.output, "w") as f:
                f.write(response)
            print(f"Response written to {args.output}")
        else:
            print(response)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()