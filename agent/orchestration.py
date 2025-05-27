import json


class AgentSwarm:
    def __init__(self, agent_type):
        self.agent_type = agent_type
        self.workflows = {
            "code": "projects/cherry-ai-project/locations/us-central1/workflows/code-agent",
            "test": "projects/cherry-ai-project/locations/us-central1/workflows/test-agent",
            "debug": "projects/cherry-ai-project/locations/us-central1/workflows/debug-agent",
        }

    def execute(self, input_data):
        workflow = self.workflows.get(self.agent_type)
        if workflow:
            workflows.create_execution(
                workflow=workflow,
                input_data={"input": json.dumps({"project": "cherry-ai-project"})},
            )
