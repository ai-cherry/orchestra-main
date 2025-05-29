import json

from google.cloud.workflows import executions_v1
from google.cloud.workflows_v1.types import Execution


class AgentSwarm:
    def __init__(self, agent_type):
        self.agent_type = agent_type
        self.workflows = {
            "code": "projects/cherry-ai-project/locations/us-central1/workflows/code-agent",
            "test": "projects/cherry-ai-project/locations/us-central1/workflows/test-agent",
            "debug": "projects/cherry-ai-project/locations/us-central1/workflows/debug-agent",
        }
        self.executions_client = executions_v1.ExecutionsClient()

    def execute(self, input_data):
        parent_workflow_path = self.workflows.get(self.agent_type)
        if parent_workflow_path:
            execution_input = json.dumps({"project": "cherry-ai-project", "input_data": input_data})
            execution = Execution(argument=execution_input)
            try:
                response = self.executions_client.create_execution(parent=parent_workflow_path, execution=execution)
                print(f"Created execution: {response.name}")
            except Exception as e:
                print(f"Error creating workflow execution: {e}")
