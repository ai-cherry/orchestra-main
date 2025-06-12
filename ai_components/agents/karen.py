from core.secrets_manager import secrets

openai_key = secrets.get_secret("OPENAI_API_KEY")
notion_token = secrets.get_secret("NOTION_API_TOKEN") 