# GCP IDE Sync

A comprehensive system for synchronizing between GitHub Codespaces and GCP Cloud Workstations, providing seamless development experience across environments.

## Overview

GCP IDE Sync enables developers to work seamlessly between GitHub Codespaces and Google Cloud Platform Cloud Workstations. It provides:

- **File Synchronization**: Real-time bidirectional file sync between environments
- **Terminal Access**: Remote terminal sessions with GCP Cloud Workstations
- **Environment Management**: Start, stop, and monitor GCP Cloud Workstations
- **Secure Authentication**: Integration with Google Cloud authentication

## Architecture

The system consists of two main components:

1. **VS Code Extension**: Client-side extension that integrates with VS Code in GitHub Codespaces
2. **Sync Service**: Server-side service deployed to Cloud Run that handles synchronization and terminal sessions

```
┌─────────────────┐                  ┌─────────────────┐
│                 │                  │                 │
│  VS Code        │                  │  GCP Cloud      │
│  Extension      │◄────────────────►│  Workstation    │
│  (Codespaces)   │                  │                 │
│                 │                  │                 │
└────────┬────────┘                  └─────────────────┘
         │
         │
         ▼
┌─────────────────┐
│                 │
│  Sync Service   │
│  (Cloud Run)    │
│                 │
└─────────────────┘
```

## Components

### VS Code Extension

The VS Code extension provides the user interface for the synchronization system:

- Status bar integration for connection status
- File synchronization on save
- Terminal integration for remote sessions
- Tree view for managing GCP Cloud Workstations

### Sync Service

The sync service handles the server-side operations:

- Authentication with Google Cloud
- File synchronization via REST API
- Terminal sessions via WebSockets
- Environment management via Google Cloud APIs

## Setup

### Prerequisites

- Google Cloud Platform account with Cloud Workstations enabled
- GitHub account with Codespaces access
- Service account with appropriate permissions

### Installation

#### VS Code Extension

1. Install the extension from the VS Code Marketplace
2. Open the command palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
3. Run `GCP IDE Sync: Connect to GCP Workstation`
4. Follow the authentication prompts

#### Sync Service

Deploy the sync service to Cloud Run:

```bash
# Clone the repository
git clone https://github.com/your-org/gcp-ide-sync.git
cd gcp-ide-sync

# Deploy using Terraform
cd terraform
terraform init
terraform apply
```

Alternatively, you can use the GitHub Actions workflow to deploy the service:

1. Fork the repository
2. Set up the required GitHub secrets:
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GCP_REGION`: Your Google Cloud region
   - `GCP_SA_KEY`: Your service account key (JSON)
3. Push to the main branch to trigger the deployment

## Usage

### Connecting to a Workstation

1. Open the command palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Run `GCP IDE Sync: Connect to GCP Workstation`
3. Select a workstation from the list
4. If the workstation is not running, you'll be prompted to start it

### Synchronizing Files

Files are automatically synchronized when:

- You save a file in VS Code
- You create a new file
- You delete a file

You can also manually synchronize all files:

1. Open the command palette
2. Run `GCP IDE Sync: Sync Files`

### Using the Terminal

To open a terminal connected to the remote workstation:

1. Open the command palette
2. Run `GCP IDE Sync: Open Remote Terminal`

### Managing Workstations

Use the GCP Workstations view in the activity bar to:

- View workstation status
- Start workstations
- Stop workstations

## Configuration

The extension can be configured through VS Code settings:

- `gcp-ide-sync.projectId`: GCP project ID
- `gcp-ide-sync.region`: GCP region
- `gcp-ide-sync.serviceAccountKeyPath`: Path to service account key file
- `gcp-ide-sync.syncInterval`: File sync interval in milliseconds
- `gcp-ide-sync.autoSync`: Enable/disable automatic file synchronization

## Development

### Building the VS Code Extension

```bash
cd gcp-ide-sync/vscode-extension
npm install
npm run compile
```

### Building the Sync Service

```bash
cd gcp-ide-sync/sync-service
npm install
npm run build
```

### Running Locally

```bash
# Start the sync service
cd gcp-ide-sync/sync-service
npm run dev

# Start the VS Code extension
cd gcp-ide-sync/vscode-extension
npm run watch
```

## Security

The system uses several security mechanisms:

- Google Cloud authentication for API access
- JWT tokens for WebSocket authentication
- HTTPS for all communication
- Secret Manager for storing sensitive values

## License

MIT