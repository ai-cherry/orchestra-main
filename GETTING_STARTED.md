# Getting Started with Orchestra AI

This guide will help you quickly deploy both the Figma webhook integration and a functional LLM chat interface, even before your full website is ready.

## Quick Deployment Overview

You can deploy both components independently:

1. **LLM Chat Interface**: A simple but functional chat interface to test your LLM strategy
2. **Figma Webhook Integration**: The infrastructure to automate deployments from Figma changes

Both can be deployed now, even if your website and Figma workspace aren't fully set up yet.

## Deploying the LLM Chat Interface

This deploys a simple but professional chat interface that lets you test different LLM models.

```bash
# From the project root
cd llm-chat
chmod +x deploy-chat-interface.sh
./deploy-chat-interface.sh --project=YOUR_GCP_PROJECT_ID
```

The deployment script will:

- Create a Google Cloud Storage bucket configured for website hosting
- Upload the HTML/CSS/JS chat interface
- Configure proper permissions and cache settings
- Provide you with a public URL for immediate access

### Features of the Chat Interface

- **Multiple LLM Models**: Select from OpenAI, Claude, Gemini, or Llama models
- **Local API Key Storage**: Securely stored in the browser, never sent to servers
- **Figma Integration**: Shows notifications when Figma designs change
- **Modern, Responsive Design**: Works on desktop, tablet, and mobile
- **Markdown Support**: Formats messages with bold, italic, code blocks, etc.

### Connecting to Real LLM APIs

The chat interface includes placeholder code for LLM API connections. To use real APIs:

1. Open `index.html` in your editor
2. Find the `callLLMAPI()` function
3. Uncomment and modify the API call code to use your preferred provider
4. Redeploy the updated file

## Deploying the Figma Webhook Integration

This sets up the infrastructure for automating deployments from Figma changes:

```bash
# Deploy the webhook handler to Google Cloud Run
./scripts/deploy_webhook_to_cloud_run.sh --project=YOUR_GCP_PROJECT_ID

# Set up and register the Figma webhook
./scripts/setup_figma_webhook.sh

# Link GitHub with your GCP project
./scripts/update_github_org_secrets.sh
```

### Testing the Integration

Once deployed, you can test the webhook integration without modifying your actual codebase:

```bash
# Test the webhook with simulated Figma events
./scripts/test_figma_webhook.js --url=YOUR_WEBHOOK_URL
```

## Integrating Both Components

To have the LLM chat interface receive actual Figma updates:

1. Deploy both components following the instructions above
2. In the GitHub workflow file (`.github/workflows/figma-triggered-deploy.yml`), add a step to notify the chat interface:

```yaml
- name: Notify Chat Interface
  run: |
    curl -X POST -H "Content-Type: application/json" \
      "https://YOUR_CHAT_INTERFACE_NOTIFICATION_ENDPOINT" \
      -d '{"event": "figma-update", "message": "Design updated: ${{ github.event.client_payload.file_name }}"}'
```

## Production Deployment Timeline

| Component            | Deployment Time | Dependencies      |
| -------------------- | --------------- | ----------------- |
| LLM Chat Interface   | ~10 minutes     | GCP account       |
| Webhook Handler      | ~1-2 hours      | GCP account       |
| GitHub Workflow      | ~30 minutes     | GitHub repository |
| Complete Integration | ~3 hours        | All of the above  |

## Next Steps

1. **Deploy the LLM Chat Interface** to start testing your LLM strategy
2. **Set up the Figma Webhook Infrastructure** to prepare for design automation
3. **Connect Real APIs** to the chat interface
4. **Test with Sample Figma Files** before your actual design system is ready

Refer to `EARLY_DEPLOYMENT_STRATEGY.md` for guidance on deploying before your website and Figma workspace are fully set up.

For detailed production requirements, see `PRODUCTION_DEPLOYMENT_CHECKLIST.md`.
