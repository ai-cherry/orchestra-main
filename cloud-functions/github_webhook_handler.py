# GitHub Webhook Handler for GCP Cloud Functions
# This script processes GitHub webhooks and triggers actions in GCP

import hashlib
import hmac
import json
import os

import google.cloud.logging
from flask import Flask, jsonify, request
from google.cloud import pubsub_v1, secretmanager, storage

app = Flask(__name__)

# Configure logging
client = google.cloud.logging.Client()
client.setup_logging()

# Environment variables
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
GITHUB_SECRET_NAME = os.environ.get("GITHUB_SECRET_NAME", "github-webhook-secret")
PUBSUB_TOPIC = os.environ.get("PUBSUB_TOPIC", "github-events")
BUCKET_NAME = os.environ.get("BUCKET_NAME", f"{PROJECT_ID}-github-artifacts")

# Initialize clients
publisher = pubsub_v1.PublisherClient()
secret_client = secretmanager.SecretManagerServiceClient()
storage_client = storage.Client()


def get_webhook_secret():
    """Get GitHub webhook secret from Secret Manager."""
    name = f"projects/{PROJECT_ID}/secrets/{GITHUB_SECRET_NAME}/versions/latest"
    response = secret_client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def verify_signature(payload, signature_header):
    """Verify the webhook signature."""
    if not signature_header:
        app.logger.error("No signature header")
        return False

    webhook_secret = get_webhook_secret()
    hmac_gen = hmac.new(webhook_secret.encode("utf-8"), payload, hashlib.sha256)
    expected_signature = f"sha256={hmac_gen.hexdigest()}"
    return hmac.compare_digest(signature_header, expected_signature)


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    """Handle GitHub webhook events."""
    # Get the signature header
    signature_header = request.headers.get("X-Hub-Signature-256")

    # Verify the signature
    if not verify_signature(request.data, signature_header):
        app.logger.error("Invalid webhook signature")
        return jsonify({"error": "Invalid signature"}), 401

    # Parse the payload
    payload = json.loads(request.data)
    event_type = request.headers.get("X-GitHub-Event")

    # Log the event
    app.logger.info(f"Received GitHub event: {event_type}")

    # Store the payload in GCS for archiving
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        repo_name = payload.get("repository", {}).get("full_name", "unknown")
        event_id = request.headers.get("X-GitHub-Delivery", "unknown")
        blob = bucket.blob(f"events/{repo_name}/{event_type}/{event_id}.json")
        blob.upload_from_string(json.dumps(payload))
        app.logger.info(f"Stored event in GCS: {blob.name}")
    except Exception as e:
        app.logger.error(f"Error storing event in GCS: {e}")

    # Process based on event type
    handlers = {
        "push": handle_push_event,
        "pull_request": handle_pr_event,
        "issue_comment": handle_comment_event,
        "workflow_job": handle_workflow_event,
        "pull_request_review": handle_review_event,
        "repository": handle_repository_event,
        "codespaces": handle_codespaces_event,
    }

    # Call the appropriate handler or use default
    if event_type in handlers:
        return handlers[event_type](payload)
    else:
        # For unhandled events, just publish to PubSub
        return publish_to_pubsub(event_type, payload)


def handle_push_event(payload):
    """Handle GitHub push events."""
    # Extract relevant information
    repo_name = payload.get("repository", {}).get("full_name")
    branch = payload.get("ref", "").replace("refs/heads/", "")
    commits = payload.get("commits", [])

    app.logger.info(
        f"Push to {repo_name} on branch {branch} with {len(commits)} commits"
    )

    # Check if this is a push to main/master
    if branch in ("main", "master"):
        # Trigger Cloud Build for deployment
        trigger_cloud_build(repo_name, branch)

    # Publish event to PubSub
    return publish_to_pubsub("push", payload)


def handle_pr_event(payload):
    """Handle GitHub pull request events."""
    # Extract relevant information
    action = payload.get("action")
    repo_name = payload.get("repository", {}).get("full_name")
    pr_number = payload.get("number")

    app.logger.info(f"PR {action} in {repo_name}: PR #{pr_number}")

    # If a PR is opened or synchronized, trigger Cloud Build
    if action in ("opened", "synchronize"):
        # Extract PR head information
        head_ref = payload.get("pull_request", {}).get("head", {}).get("ref")
        trigger_cloud_build(repo_name, head_ref, pr_number=pr_number)

    # Create a Codespace for review if enabled and PR was opened
    if action == "opened" and os.environ.get("AUTO_CREATE_CODESPACE") == "true":
        create_review_codespace(payload)

    # Publish event to PubSub
    return publish_to_pubsub("pull_request", payload)


def handle_comment_event(payload):
    """Handle GitHub issue/PR comment events."""
    # Extract relevant information
    action = payload.get("action")
    repo_name = payload.get("repository", {}).get("full_name")
    issue_number = payload.get("issue", {}).get("number")
    comment = payload.get("comment", {}).get("body", "")

    app.logger.info(f"Comment {action} on {repo_name} #{issue_number}")

    # Check for command comments
    commands = {
        "/deploy": trigger_deployment,
        "/approve": approve_pr,
        "/terraform-plan": run_terraform_plan,
        "/create-codespace": create_review_codespace,
    }

    for cmd, handler in commands.items():
        if comment.strip().startswith(cmd):
            return handler(payload)

    # Publish event to PubSub
    return publish_to_pubsub("issue_comment", payload)


def handle_workflow_event(payload):
    """Handle GitHub Actions workflow events."""
    # Extract relevant information
    action = payload.get("action")
    workflow_name = payload.get("workflow_job", {}).get("name")
    repo_name = payload.get("repository", {}).get("full_name")

    app.logger.info(f"Workflow {workflow_name} {action} in {repo_name}")

    # Publish event to PubSub
    return publish_to_pubsub("workflow_job", payload)


def handle_review_event(payload):
    """Handle GitHub pull request review events."""
    # Extract relevant information
    action = payload.get("action")
    repo_name = payload.get("repository", {}).get("full_name")
    pr_number = payload.get("pull_request", {}).get("number")
    state = payload.get("review", {}).get("state")

    app.logger.info(f"Review {action} on {repo_name} PR #{pr_number}: {state}")

    # If approved and auto-merge is enabled, merge the PR
    if state == "approved" and os.environ.get("AUTO_MERGE_APPROVED") == "true":
        merge_approved_pr(payload)

    # Publish event to PubSub
    return publish_to_pubsub("pull_request_review", payload)


def handle_repository_event(payload):
    """Handle GitHub repository events."""
    # Extract relevant information
    action = payload.get("action")
    repo_name = payload.get("repository", {}).get("full_name")

    app.logger.info(f"Repository {action}: {repo_name}")

    # If a new repo is created, initialize infrastructure
    if action == "created":
        initialize_repository(payload)

    # Publish event to PubSub
    return publish_to_pubsub("repository", payload)


def handle_codespaces_event(payload):
    """Handle GitHub Codespaces events."""
    # Extract relevant information
    action = payload.get("action")
    repo_name = payload.get("repository", {}).get("full_name")
    codespace_name = payload.get("codespace", {}).get("name")

    app.logger.info(f"Codespace {action}: {codespace_name} in {repo_name}")

    # If a codespace is created, configure it with GCP credentials
    if action == "created":
        setup_codespace_gcp_auth(payload)

    # Publish event to PubSub
    return publish_to_pubsub("codespaces", payload)


def trigger_cloud_build(repo_name, branch, pr_number=None):
    """Trigger a Cloud Build job."""
    # Build the Cloud Build trigger request
    substitutions = {"_BRANCH_NAME": branch, "_REPO_NAME": repo_name}

    if pr_number:
        substitutions["_PR_NUMBER"] = str(pr_number)

    message = {
        "repo_name": repo_name,
        "branch": branch,
        "pr_number": pr_number,
        "action": "trigger_build",
        "substitutions": substitutions,
    }

    # Publish to PubSub for Cloud Build to pick up
    topic_path = publisher.topic_path(PROJECT_ID, "cloud-build-triggers")
    future = publisher.publish(
        topic_path,
        json.dumps(message).encode("utf-8"),
        origin="github-webhook",
        event_type="build_trigger",
    )

    app.logger.info(
        f"Triggered Cloud Build for {repo_name}/{branch}: {future.result()}"
    )
    return jsonify({"status": "success", "message": "Build triggered"})


def publish_to_pubsub(event_type, payload):
    """Publish an event to PubSub."""
    topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)

    # Prepare message data
    message_data = {"event_type": event_type, "payload": payload}

    # Publish message
    future = publisher.publish(
        topic_path,
        json.dumps(message_data).encode("utf-8"),
        event_type=event_type,
        origin="github-webhook",
    )

    app.logger.info(f"Published {event_type} event to PubSub: {future.result()}")
    return jsonify({"status": "success", "message": "Event processed"})


def create_review_codespace(payload: dict) -> None:
    print(
        f"Placeholder: Creating review codespace for PR #{payload.get('pull_request', {}).get('number')}"
    )


def trigger_deployment(payload: dict) -> None:
    print(
        f"Placeholder: Triggering deployment for {payload.get('repository', {}).get('full_name')}"
    )


def approve_pr(payload: dict) -> None:
    print(
        f"Placeholder: Approving PR for {payload.get('repository', {}).get('full_name')}"
    )


def run_terraform_plan(payload: dict) -> None:
    print(
        f"Placeholder: Running terraform plan for {payload.get('repository', {}).get('full_name')}"
    )


def merge_approved_pr(payload: dict) -> None:
    print(
        f"Placeholder: Merging approved PR for {payload.get('repository', {}).get('full_name')}"
    )


def initialize_repository(payload: dict) -> None:
    print(
        f"Placeholder: Initializing repository for {payload.get('repository', {}).get('full_name')}"
    )


def setup_codespace_gcp_auth(payload: dict) -> None:
    print(
        f"Placeholder: Setting up codespace GCP auth for {payload.get('repository', {}).get('full_name')}"
    )


# Execute the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
