#!/bin/bash

# Orchestra AI GPU Acceleration Configuration
# Enables NVIDIA GPU support for MCP Memory server

set -e

echo "🚀 Configuring GPU acceleration for Orchestra AI..."

# Install NVIDIA Container Toolkit on Lambda Labs instance
ssh ubuntu@150.136.94.139 << 'REMOTE_GPU_SETUP'
    echo "📦 Installing NVIDIA Container Toolkit..."
    
    # Add NVIDIA package repository
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
    
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    
    # Configure Docker to use NVIDIA runtime
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
    
    # Test GPU access
    docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
    
    echo "✅ GPU acceleration configured successfully!"
REMOTE_GPU_SETUP

# Update MCP Memory deployment to use GPU
kubectl patch deployment mcp-memory -n orchestra -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "mcp-memory",
          "image": "nvidia/cuda:11.8-devel-ubuntu20.04",
          "command": ["/bin/bash", "-c"],
          "args": [
            "apt-get update && apt-get install -y python3 python3-pip git curl && pip3 install torch transformers sentence-transformers faiss-gpu && git clone https://github.com/ai-cherry/orchestra-main.git /app && cd /app && python3 main_mcp.py --port 8003"
          ],
          "resources": {
            "limits": {
              "nvidia.com/gpu": "1"
            }
          }
        }]
      }
    }
  }
}'

echo "🎯 GPU acceleration enabled for MCP Memory server!"
echo "📊 Monitoring GPU usage with nvidia-smi..."

