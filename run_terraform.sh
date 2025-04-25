#!/bin/bash
# This script creates a Docker container with Terraform and runs Terraform commands

# Create Dockerfile
cat > Dockerfile.terraform << EOF
FROM hashicorp/terraform:1.5.0

RUN apk add --no-cache bash curl jq python3

# Install Google Cloud SDK
RUN curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz && \
    tar -xf google-cloud-cli-linux-x86_64.tar.gz && \
    ./google-cloud-sdk/install.sh --quiet && \
    rm google-cloud-cli-linux-x86_64.tar.gz

ENV PATH=$PATH:/google-cloud-sdk/bin

WORKDIR /workspace

COPY . .
EOF

# Build Docker image
echo "Building Terraform Docker image..."
docker build -t terraform-gcp -f Dockerfile.terraform .

# Run Terraform init
echo "Running Terraform init..."
docker run -v $(pwd):/workspace -v /tmp/gsa-key.json:/tmp/gsa-key.json -w /workspace/dev terraform-gcp terraform init

# Run Terraform plan
echo "Running Terraform plan..."
docker run -v $(pwd):/workspace -v /tmp/gsa-key.json:/tmp/gsa-key.json -w /workspace/dev terraform-gcp terraform plan -out=tfplan

echo "To apply the Terraform plan, run:"
echo "docker run -v $(pwd):/workspace -v /tmp/gsa-key.json:/tmp/gsa-key.json -w /workspace/dev terraform-gcp terraform apply tfplan"
