from google.cloud import secretmanager

class TurboOrchestrator:
    def __init__(self):
        self.secret_client = secretmanager.SecretManagerServiceClient()
        
    def get_all_secrets(self):
        return {
            "OPENAI": self._get_secret("OPENAI_API_KEY"),
            "ANTHROPIC": self._get_secret("ANTHROPIC_API_KEY"),
            "PORTKEY": self._get_secret("PORTKEY_API_KEY")
        }
        
    def _get_secret(self, name):
        return self.secret_client.access_secret_version(
            name=f"projects/agi-baby-cherry/secrets/{name}/versions/latest"
        ).payload.data.decode('UTF-8')