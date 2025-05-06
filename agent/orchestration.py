from google.cloud import workflows
import json

class AgentSwarm:
    def __init__(self):
        self.workflow_client = workflows.WorkflowsClient()

    def create_agent_task(self, task_type):
        """Dynamic agent routing"""
        workflow_map = {
            "code": "projects/agi-baby-cherry/locations/us-central1/workflows/code-agent",
            "test": "projects/agi-baby-cherry/locations/us-central1/workflows/test-agent",
            "debug": "projects/agi-baby-cherry/locations/us-central1/workflows/debug-agent"
        }

        return self.workflow_client.run_workflow(
            request={
                "name": workflow_map[task_type],
                "input": json.dumps({"project": "agi-baby-cherry"})
            }
        )
