"""
LLM-powered Log Analyzer for Orchestra Monitoring System.

This module analyzes logs from Cloud Storage using Vertex AI to:
1. Detect anomalies and patterns in log data
2. Suggest fixes for common issues
3. Create GitHub issues for significant problems
4. Categorize and prioritize alerts
"""

import base64
import functions_framework
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

import google.auth
import google.cloud.storage as storage
import google.cloud.logging as logging_client
import requests
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
PROJECT_ID = os.environ.get("PROJECT_ID")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
VERTEX_AI_REGION = os.environ.get("VERTEX_AI_REGION", "us-central1")
MODEL_ID = os.environ.get("MODEL_ID", "text-bison@002")
GITHUB_REPO = os.environ.get("GITHUB_REPO")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# Initialize clients
storage_client = storage.Client()
logging_client = logging_client.Client()


@functions_framework.cloud_event
def analyze_logs(cloud_event):
    """
    Cloud Function triggered by a finalized log file in Cloud Storage.

    Args:
        cloud_event: The Cloud Event containing the storage event information
    """
    try:
        # Extract bucket and file information
        payload = cloud_event.data
        bucket_name = payload["bucket"]
        file_name = payload["name"]

        logger.info(f"Processing log file: gs://{bucket_name}/{file_name}")

        # Skip if not a log file or already processed
        if not file_name.endswith(".json") or file_name.startswith("processed_"):
            logger.info(
                f"Skipping file: {file_name} (not a log file or already processed)"
            )
            return

        # Read log data from the file
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        log_data = blob.download_as_text()

        # Parse and analyze logs
        log_entries = parse_log_data(log_data)
        if not log_entries:
            logger.info("No valid log entries found in file")
            return

        analysis_results = analyze_log_entries(log_entries)

        # Take actions based on analysis results
        handle_analysis_results(analysis_results, log_entries)

        # Mark file as processed
        processed_blob = bucket.blob(f"processed_{file_name}")
        processed_blob.upload_from_string(log_data)
        blob.delete()

        logger.info(f"Successfully processed log file: {file_name}")

    except Exception as e:
        logger.error(f"Error processing log file: {str(e)}", exc_info=True)
        raise


def parse_log_data(log_data: str) -> List[Dict]:
    """
    Parse log data from the exported log file.

    Args:
        log_data: Raw log data as a string

    Returns:
        List of parsed log entry dictionaries
    """
    log_entries = []

    try:
        # Handle different log formats
        if log_data.startswith("{"):
            # JSON format
            lines = log_data.strip().split("\n")
            for line in lines:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        log_entries.append(entry)
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Failed to parse log line as JSON: {line[:100]}..."
                        )
        else:
            # Assume text format
            lines = log_data.strip().split("\n")
            for line in lines:
                if line.strip():
                    log_entries.append({"textPayload": line})

    except Exception as e:
        logger.error(f"Error parsing log data: {str(e)}", exc_info=True)

    return log_entries


def analyze_log_entries(log_entries: List[Dict]) -> Dict[str, Any]:
    """
    Analyze log entries using Vertex AI LLM models.

    Args:
        log_entries: List of parsed log entries

    Returns:
        Analysis results containing patterns, issues, and suggested fixes
    """
    # Prepare logs for analysis
    log_text = prepare_logs_for_analysis(log_entries)

    # Call Vertex AI for analysis
    analysis = query_vertex_ai_model(log_text)

    # Parse the analysis results
    return parse_analysis_results(analysis)


def prepare_logs_for_analysis(log_entries: List[Dict]) -> str:
    """
    Prepare log entries for LLM analysis by formatting them appropriately.

    Args:
        log_entries: List of parsed log entries

    Returns:
        Formatted log text for analysis
    """
    # Extract the most relevant parts from the logs
    formatted_logs = []

    for entry in log_entries:
        try:
            timestamp = entry.get("timestamp", "UNKNOWN_TIME")
            severity = entry.get("severity", "INFO")

            # Extract the message from different possible formats
            message = None
            if "textPayload" in entry:
                message = entry["textPayload"]
            elif "jsonPayload" in entry:
                # For JSON payloads, look for common message fields
                json_payload = entry["jsonPayload"]
                message = (
                    json_payload.get("message")
                    or json_payload.get("msg")
                    or str(json_payload)
                )
            elif "protoPayload" in entry:
                message = str(entry["protoPayload"])

            # If we found a message, add it to the formatted logs
            if message:
                # Clean up and truncate long messages
                message = re.sub(r"\s+", " ", message)
                if len(message) > 500:
                    message = message[:497] + "..."

                formatted_entry = f"[{timestamp}] {severity}: {message}"
                formatted_logs.append(formatted_entry)

        except Exception as e:
            logger.warning(f"Error formatting log entry: {str(e)}")

    # Limit to the most recent logs if there are too many
    if len(formatted_logs) > 100:
        formatted_logs = formatted_logs[-100:]

    # Add context information
    context = f"""
    ANALYSIS CONTEXT:
    - Environment: {ENVIRONMENT}
    - Project: {PROJECT_ID}
    - Timestamp: {datetime.now().isoformat()}
    - Number of log entries: {len(log_entries)}
    
    TASK:
    Analyze the following logs and provide:
    1. A summary of the main issues found
    2. Potential root causes for any errors or warnings
    3. Recommended fixes with specific code or configuration changes
    4. Whether this issue requires a GitHub issue (yes/no)
    5. If yes, what should be the title and priority of the GitHub issue (high/medium/low)
    
    LOG ENTRIES:
    """

    return context + "\n".join(formatted_logs)


def query_vertex_ai_model(prompt: str) -> str:
    """
    Query Vertex AI to analyze the logs using the specified model.

    Args:
        prompt: The formatted log analysis prompt

    Returns:
        The model's analysis response
    """
    # Initialize the Vertex AI SDK
    aiplatform.init(project=PROJECT_ID, location=VERTEX_AI_REGION)

    # Set parameters for the model
    parameters = {
        "temperature": 0.2,
        "max_output_tokens": 1024,
        "top_p": 0.8,
        "top_k": 40,
    }

    try:
        # Get the model resource name
        model = aiplatform.TextGenerationModel.from_pretrained(MODEL_ID)

        # Make the prediction request
        response = model.predict(prompt=prompt, **parameters)

        # Return the prediction text
        return response.text

    except Exception as e:
        logger.error(f"Error querying Vertex AI: {str(e)}", exc_info=True)
        return f"Error analyzing logs: {str(e)}"


def parse_analysis_results(analysis: str) -> Dict[str, Any]:
    """
    Parse the analysis results from the LLM response.

    Args:
        analysis: Raw analysis text from the LLM

    Returns:
        Structured analysis results
    """
    results = {
        "summary": "",
        "root_causes": [],
        "recommended_fixes": [],
        "create_github_issue": False,
        "github_issue": {"title": "", "priority": "medium", "description": ""},
    }

    try:
        # Extract summary (first paragraph)
        summary_match = re.search(
            r"^(.+?)(?:\n\n|\n(?:[0-9]+\.|\-|$))", analysis, re.DOTALL | re.MULTILINE
        )
        if summary_match:
            results["summary"] = summary_match.group(1).strip()

        # Look for root causes
        root_causes_section = re.search(
            r"(?:root causes|potential causes):(.*?)(?:\n\n|\n[0-9]+\.)",
            analysis,
            re.IGNORECASE | re.DOTALL,
        )
        if root_causes_section:
            causes_text = root_causes_section.group(1).strip()
            # Extract bullet points or numbered items
            causes = re.findall(
                r"(?:^|\n)(?:\-|\*|[0-9]+\.)\s*(.+?)(?:\n|$)", causes_text
            )
            if causes:
                results["root_causes"] = [cause.strip() for cause in causes]

        # Look for recommended fixes
        fixes_section = re.search(
            r"(?:recommended fixes|suggested fixes|recommendations):(.*?)(?:\n\n|\n[0-9]+\.|\Z)",
            analysis,
            re.IGNORECASE | re.DOTALL,
        )
        if fixes_section:
            fixes_text = fixes_section.group(1).strip()
            # Extract bullet points or numbered items
            fixes = re.findall(
                r"(?:^|\n)(?:\-|\*|[0-9]+\.)\s*(.+?)(?:\n|$)", fixes_text
            )
            if fixes:
                results["recommended_fixes"] = [fix.strip() for fix in fixes]

        # Determine if GitHub issue should be created
        github_match = re.search(
            r"(?:github issue|create (?:a |an )?issue):\s*(yes|no)",
            analysis,
            re.IGNORECASE,
        )
        if github_match and github_match.group(1).lower() == "yes":
            results["create_github_issue"] = True

            # Extract GitHub issue title
            title_match = re.search(
                r"(?:issue |github issue )?title:\s*(.+?)(?:\n|$)",
                analysis,
                re.IGNORECASE,
            )
            if title_match:
                results["github_issue"]["title"] = title_match.group(1).strip()
            else:
                # Use the summary as the title if no specific title is found
                results["github_issue"]["title"] = results["summary"]

            # Extract priority
            priority_match = re.search(
                r"priority:\s*(high|medium|low)", analysis, re.IGNORECASE
            )
            if priority_match:
                results["github_issue"]["priority"] = priority_match.group(1).lower()

            # Use the full analysis as the description
            results["github_issue"]["description"] = analysis

    except Exception as e:
        logger.error(f"Error parsing analysis results: {str(e)}", exc_info=True)

    return results


def handle_analysis_results(analysis_results: Dict[str, Any], log_entries: List[Dict]):
    """
    Take appropriate actions based on the analysis results.

    Args:
        analysis_results: Structured analysis results
        log_entries: Original log entries
    """
    # Log the analysis summary
    logger.info(f"Log Analysis Summary: {analysis_results['summary']}")

    # Create GitHub issue if recommended
    if analysis_results["create_github_issue"]:
        create_github_issue(analysis_results["github_issue"])

    # Record analysis in Cloud Logging for future reference
    record_analysis_in_logs(analysis_results, log_entries)


def create_github_issue(issue_data: Dict[str, str]):
    """
    Create a GitHub issue based on the analysis.

    Args:
        issue_data: GitHub issue data including title, description, and priority
    """
    if not GITHUB_REPO or not GITHUB_TOKEN:
        logger.error("GitHub repository or token not configured")
        return

    try:
        # Prepare the issue data
        url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Format the description with markdown
        description = f"""
## AI-Generated Issue from Log Analysis

{issue_data["description"]}

---
*This issue was automatically created by the Orchestra monitoring system based on log analysis.*
*Priority: {issue_data["priority"].upper()}*
*Environment: {ENVIRONMENT}*
*Generated at: {datetime.now().isoformat()}*
        """

        # Add labels based on priority and source
        labels = [
            "ai-generated",
            f"priority-{issue_data['priority']}",
            "monitoring-alert",
            ENVIRONMENT,
        ]

        # Create the issue
        payload = {"title": issue_data["title"], "body": description, "labels": labels}

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code >= 200 and response.status_code < 300:
            issue_url = response.json().get("html_url")
            logger.info(f"Created GitHub issue: {issue_url}")
        else:
            logger.error(
                f"Failed to create GitHub issue: {response.status_code}, {response.text}"
            )

    except Exception as e:
        logger.error(f"Error creating GitHub issue: {str(e)}", exc_info=True)


def record_analysis_in_logs(analysis_results: Dict[str, Any], log_entries: List[Dict]):
    """
    Record the analysis results in Cloud Logging for future reference.

    Args:
        analysis_results: Structured analysis results
        log_entries: Original log entries
    """
    try:
        # Create structured log entry
        logger_client = logging_client.logger("log-analysis-results")

        # Extract service names from log entries if available
        services = set()
        for entry in log_entries:
            if "resource" in entry and "labels" in entry["resource"]:
                service_name = entry["resource"]["labels"].get("service_name")
                if service_name:
                    services.add(service_name)

        # Create the structured log entry
        logger_client.log_struct(
            {
                "analysis_summary": analysis_results["summary"],
                "root_causes": analysis_results["root_causes"],
                "recommended_fixes": analysis_results["recommended_fixes"],
                "github_issue_created": analysis_results["create_github_issue"],
                "github_issue_title": analysis_results["github_issue"]["title"]
                if analysis_results["create_github_issue"]
                else None,
                "github_issue_priority": analysis_results["github_issue"]["priority"]
                if analysis_results["create_github_issue"]
                else None,
                "affected_services": list(services),
                "environment": ENVIRONMENT,
                "timestamp": datetime.now().isoformat(),
            },
            severity="INFO",
        )

    except Exception as e:
        logger.error(f"Error recording analysis in logs: {str(e)}", exc_info=True)


if __name__ == "__main__":
    # For local testing
    print("This script is intended to be run as a Cloud Function")
