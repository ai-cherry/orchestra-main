{
"image": "mcr.microsoft.com/devcontainers/python:3.11",
"features": {
"ghcr.io/devcontainers-contrib/features/poetry:2": {},
"ghcr.io/devcontainers/features/terraform:1": {
"version": "1.5.x"
},
"ghcr.io/devcontainers/features/docker-outside-of-docker:1": {}
},
"customizations": {
"vscode": {
"extensions": [
"ms-python.python",
"hashicorp.terraform",
"charliermarsh.ruff",
"github.copilot",
"github.copilot-chat",
"GoogleCloudTools.cloudcode",
"GoogleCloudTools.cloudcode-gemini",
"Rooservices.roo-ai",
"Cline.cline-vscode"
],
"settings": {
"geminiCodeAssist.projectId": "cherry-ai-project",
"geminiCodeAssist.contextAware": true,
"geminiCodeAssist.codeReview.enabled": true,
"cloudcode.duetAI.project": "cherry-ai-project",
"cloudcode.project": "cherry-ai-project",
"roo.mode": "turbo",
"cline.apiSource": "gcp-secret-manager"
}
}
},
"postCreateCommand": "poetry install --with dev"
}
