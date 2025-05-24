from google.cloud import aiplatform
import portkey
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class LLMGateway:
    def __init__(self):
        self.vertex = aiplatform.gapic.PredictionServiceClient()
        self.portkey = portkey.Client(api_key=os.getenv("PORTKEY_API_KEY"))
        logger.info("LLMGateway initialized")

    def generate(self, prompt: str) -> str:
        """Smart routing between LLM providers"""
        try:
            logger.info("Attempting to use Portkey with model gemini-pro")
            response = self.portkey.chat.completions.create(
                model="gemini-pro", messages=[{"role": "user", "content": prompt}]
            )
            logger.info("Successfully used Portkey for generation")
            return response
        except Exception as e:
            logger.warning(f"Portkey failed, falling back to Vertex AI. Error: {str(e)}")
            response = self.vertex.predict(
                endpoint=f"projects/cherry-ai-project/locations/us-west4/endpoints/gemini-pro",
                instances=[{"content": prompt}],
            ).predictions[0]
            logger.info("Successfully used Vertex AI as fallback")
            return response
