import os
import json
from flask import Flask, request, jsonify
from pulumi import automation as auto

app = Flask(__name__)

# Configuration
PULUMI_PROJECT_DIR = os.path.join(os.path.dirname(__file__), '..', 'infra')
PULUMI_STACK_NAME = "dev"  # Or make this configurable, e.g., via request param


@app.route('/deploy', methods=['POST'])
def deploy_infrastructure():
    """Endpoint to trigger a Pulumi deployment.
    Authenticates to GCP via GOOGLE_APPLICATION_CREDENTIALS env var.
    Requires PULUMI_ACCESS_TOKEN env var for Pulumi Cloud login.
    """
    try:
        # Ensure environment variables are set (basic check)
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            return jsonify({"error": "GOOGLE_APPLICATION_CREDENTIALS not set"}), 500
        if not os.getenv("PULUMI_ACCESS_TOKEN"):
            # The Pulumi Automation API will use this token if set
            # For self-managed backends, this might not be strictly necessary if already logged in
            app.logger.info(
                "PULUMI_ACCESS_TOKEN not set, relying on existing Pulumi login or anonymous access for local state.")

        app.logger.info(
            f"Attempting to deploy stack: {PULUMI_STACK_NAME} from {PULUMI_PROJECT_DIR}")

        # Create or select the stack using Pulumi Automation API
        stack = auto.select_stack(
            stack_name=PULUMI_STACK_NAME,
            project_name=None,  # Pulumi infers project name from Pulumi.yaml in work_dir
            work_dir=PULUMI_PROJECT_DIR
        )

        app.logger.info("Successfully selected/created stack.")

        # Optional: Refresh stack before update
        app.logger.info("Refreshing stack...")
        stack.refresh(on_output=app.logger.info)
        app.logger.info("Stack refresh complete.")

        # Run the equivalent of `pulumi up --yes`
        app.logger.info("Running pulumi up...")
        up_result = stack.up(on_output=app.logger.info)

        app.logger.info("Pulumi up finished.")

        return jsonify({
            "message": "Deployment successful",
            "summary": up_result.summary.resource_changes,
            "outputs": up_result.outputs
        }), 200

    except auto.StackAlreadyExistsError:
        # This typically shouldn't happen with select_stack if it selects an existing one.
        # auto.create_or_select_stack is more robust for this.
        # For simplicity, we are using select_stack assuming it exists or was init'd.
        app.logger.error("StackAlreadyExistsError - this should be handled by select_stack.")
        return jsonify({"error": "Stack already exists and select_stack failed to select it."}), 500

    except auto.ConcurrentUpdateError:
        app.logger.error("ConcurrentUpdateError: Another update is already in progress.")
        # Conflict
        return jsonify({"error": "Deployment failed: Another update is already in progress."}), 409

    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        # Consider logging traceback for debugging: import traceback; traceback.print_exc()
        return jsonify({"error": f"Deployment failed: {str(e)}"}), 500


if __name__ == '__main__':
    # Ensure the script is run from a directory where it can find ./requirements.txt for Flask and Pulumi
    # Example: python scripts/automation_api.py
    # For production, use a proper WSGI server like Gunicorn.
    app.logger.setLevel('INFO')  # Set log level
    app.run(host='0.0.0.0', port=8080, debug=True)  # debug=True for development only
