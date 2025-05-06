# Secure Figma to GitHub Webhook Integration

A comprehensive solution for automating deployments triggered by Figma design changes, following security best practices.

## Overview

This integration allows you to automatically trigger GitHub Actions workflows whenever changes are made in Figma, enabling a seamless design-to-code workflow. The system is designed with security in mind, implementing all recommended best practices for webhook handling.

## Key Features

- ✅ **Secure webhook handling** with HMAC-SHA256 signature validation
- ✅ **Repository dispatch events** for triggering GitHub Actions
- ✅ **Minimal event subscription** to reduce noise and overhead
- ✅ **Secrets management** for secure credential storage
- ✅ **Comprehensive logging** for monitoring and troubleshooting
- ✅ **HTTPS enforcement** for production deployments

## Components

This integration consists of several key components:

| Component | Description | File |
|-----------|-------------|------|
| Webhook Handler | Server that receives Figma events and triggers GitHub workflows | [`scripts/figma_webhook_handler.js`](scripts/figma_webhook_handler.js) |
| Setup Script | Interactive script to configure webhooks and store secrets | [`scripts/setup_figma_webhook.sh`](scripts/setup_figma_webhook.sh) |
| GitHub Workflow | GitHub Actions workflow triggered by webhook events | [`.github/workflows/figma-triggered-deploy.yml`](.github/workflows/figma-triggered-deploy.yml) |
| Test Script | Tool to test webhook functionality locally | [`scripts/test_figma_webhook.js`](scripts/test_figma_webhook.js) |
| Documentation | Comprehensive guide to the integration | [`docs/FIGMA_WEBHOOK_INTEGRATION.md`](docs/FIGMA_WEBHOOK_INTEGRATION.md) |

## Quick Start

### Prerequisites

- Figma account with admin access to a team
- GitHub repository with Actions enabled
- Node.js and npm installed
- GitHub CLI (`gh`) installed and authenticated

### 1. Set Up Required Dependencies

```bash
# Navigate to the scripts directory to install webhook handler dependencies
cd scripts
npm install
```

### 2. Configure the Webhook

```bash
# Run the setup script from project root
./scripts/setup_figma_webhook.sh
```

This interactive script will:
- Generate a secure webhook secret
- Register the webhook with Figma
- Store necessary secrets in GitHub repository
- Provide guidance for next steps

### 3. Deploy the Webhook Handler

For development, you can use a tunneling service like ngrok:

```bash
# Install ngrok globally
npm install -g ngrok

# Start the webhook handler
cd scripts
npm start

# In another terminal, create a tunnel to your local server
ngrok http 3000
```

For production, deploy to a secure HTTPS endpoint:
- Cloud Run on GCP
- AWS Lambda with API Gateway
- Heroku/Vercel/Netlify

### 4. Test Your Setup

Use the included test script to verify your webhook handler:

```bash
# From project root
node scripts/test_figma_webhook.js --url=https://your-webhook-url/figma-webhook
```

## Architecture

```
┌─────────┐         ┌──────────────────┐         ┌───────────────┐         ┌───────────────┐
│  Figma  │─────────┤  Webhook Server  │─────────┤  GitHub API   │─────────┤ GitHub Action │
└─────────┘         └──────────────────┘         └───────────────┘         └───────────────┘
     │                       │                          │                         │
     │                       │                          │                         │
     └───────────────────────┴──────────────────────────┴─────────────────────────┘
                      Secured with HMAC signatures, HTTPS, and encryption
```

## Security Best Practices

The following security best practices are implemented:

1. **High-Entropy Webhook Secret**: Automatically generated using `openssl rand -hex 32`
2. **HMAC-SHA256 Signatures**: Every request is validated with cryptographic signatures
3. **Timing-Safe Comparison**: Prevents timing attacks during signature validation
4. **Secure Secret Storage**: All credentials are stored in GitHub Secrets
5. **HTTPS Transport**: Required for all production deployments
6. **Minimal Event Subscription**: Only subscribes to necessary events
7. **Logging & Monitoring**: Comprehensive logging for auditing and troubleshooting

## Customizing the Integration

### Modifying the GitHub Workflow

Edit `.github/workflows/figma-triggered-deploy.yml` to customize what happens when Figma changes are detected:

- Change deployment targets (staging, production)
- Modify the assets/tokens extracted from Figma
- Add additional validation steps
- Customize notification channels

### Adding Support for Additional Figma Events

The current integration supports:

- `FILE_UPDATE` - Triggered when a file is updated
- `FILE_VERSION_UPDATE` - Triggered when a file version is created
- `LIBRARY_PUBLISH` - Triggered when a library is published

To add support for additional events, update the mapping in `scripts/figma_webhook_handler.js`.

## Monitoring and Maintenance

### Logs

Webhook events are logged to `logs/figma-webhooks.log` for monitoring and debugging.

### Secret Rotation

For maximum security, periodically rotate the webhook secret:

1. Generate a new secret with `openssl rand -hex 32`
2. Update it in GitHub Secrets and Figma webhook configuration

## Troubleshooting

Common issues and solutions:

- **Webhook not triggering**: Verify the endpoint is accessible and check the logs
- **Signature validation failing**: Ensure the webhook secret is the same in Figma and GitHub
- **GitHub Action not running**: Check GitHub permissions and repository_dispatch event type
- **Missing dependencies**: Run `npm install` in the scripts directory

## Further Reading

For more detailed information:

- [`docs/FIGMA_WEBHOOK_INTEGRATION.md`](docs/FIGMA_WEBHOOK_INTEGRATION.md) - Comprehensive documentation
- [Figma API Documentation](https://www.figma.com/developers/api) - Official Figma API docs
- [GitHub Webhooks Documentation](https://docs.github.com/en/webhooks) - Official GitHub webhook docs

## Contributing

Contributions to improve the integration are welcome. Please follow security best practices when making changes.

## License

This integration is provided under the MIT License.
