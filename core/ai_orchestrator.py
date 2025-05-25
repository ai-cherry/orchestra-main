import portkey
from google.cloud import aiplatform, secretmanager
from vertexai.preview import generative_models


class AIOrchestrator:
    def __init__(self):
        self.vertex_llm = aiplatform.gapic.PredictionServiceClient()
        self.gemini = generative_models.GenerativeModel("gemini-1.5-pro")
        self.portkey = portkey.Client(
            api_key=self._get_gcp_secret("PORTKEY_API_KEY"),
            config={"virtual_key": "vertex-agent-special"},
        )

    def generate_code(self, prompt):
        """Smart routing between AI providers"""
        try:
            # First try Gemini with full codebase context
            return self.gemini.generate_content(
                f"Consider current GCP project cherry-ai-project: {prompt}"
            ).text
        except Exception:
            # Fallback to Vertex AI
            return self.vertex_llm.predict(
                endpoint="projects/cherry-ai-project/locations/us-west4/endpoints/gemini-pro",
                instances=[{"content": prompt}],
            ).predictions[0]

    def _get_gcp_secret(self, name):
        client = secretmanager.SecretManagerServiceClient()
        return client.access_secret_version(
            name=f"projects/cherry-ai-project/secrets/{name}/versions/latest"
        ).payload.data.decode("UTF-8")
