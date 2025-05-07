#!/bin/bash
# setup_semantic_cache.sh - Configure and test Redis semantic caching for Orchestra
#
# This script sets up Redis semantic caching integration for Orchestra,
# installing dependencies and configuring the necessary components.

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENV=${1:-dev}
REDIS_URL="redis://vertex-agent@agi-baby-cherry"

# Print header
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   Setting up Redis Semantic Caching for Orchestra    ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Function to check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check if pip is installed
if ! command_exists pip; then
  echo -e "${RED}pip not found. Please install Python and pip first.${NC}"
  exit 1
fi

# Check if Python version is compatible
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
  echo -e "${RED}Python 3.8 or higher is required. Found: ${PYTHON_VERSION}${NC}"
  exit 1
fi

echo -e "${GREEN}Python ${PYTHON_VERSION} detected.${NC}"

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
  echo -e "${YELLOW}Creating virtual environment...${NC}"
  python3 -m venv venv
  echo -e "${GREEN}Virtual environment created.${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}Virtual environment activated.${NC}"

# Install dependencies
echo -e "${YELLOW}Installing required packages...${NC}"
pip install -q -U pip wheel

echo -e "${YELLOW}Installing Redis semantic caching dependencies...${NC}"
pip install -q -r semantic_cache_requirements.txt

# Optional: add to main requirements
if [ -f "requirements-consolidated.txt" ]; then
  echo -e "${YELLOW}Checking main requirements file...${NC}"
  if ! grep -q "redisvl" requirements-consolidated.txt; then
    echo -e "${YELLOW}Adding redisvl to main requirements file...${NC}"
    echo "# Semantic caching" >> requirements-consolidated.txt
    echo "redisvl>=0.0.5" >> requirements-consolidated.txt
    echo "langchain-redis>=0.1.1" >> requirements-consolidated.txt
    echo -e "${GREEN}Added Redis semantic caching packages to main requirements.${NC}"
  else
    echo -e "${GREEN}Redis semantic caching already in main requirements.${NC}"
  fi
fi

# Check for environment variables
if [ ! -f ".env" ]; then
  echo -e "${YELLOW}Creating .env file...${NC}"
  touch .env
fi

# Update .env file with Redis URL
if ! grep -q "REDIS_URL=" .env; then
  echo -e "${YELLOW}Adding REDIS_URL to .env file...${NC}"
  echo "" >> .env
  echo "# Redis Semantic Cache Configuration" >> .env
  echo "REDIS_URL=${REDIS_URL}" >> .env
  echo -e "${GREEN}Added Redis URL to .env file.${NC}"
else
  echo -e "${GREEN}Redis URL already in .env file.${NC}"
fi

# Check for Gemini API key
if ! grep -q "GEMINI_API_KEY=" .env && [ ! -f "gemini.key" ]; then
  echo -e "${YELLOW}No Gemini API key found.${NC}"
  read -p "Enter your Gemini API key (or press Enter to skip): " GEMINI_API_KEY
  
  if [ ! -z "$GEMINI_API_KEY" ]; then
    echo -e "${YELLOW}Saving Gemini API key...${NC}"
    echo "GEMINI_API_KEY=${GEMINI_API_KEY}" >> .env
    echo -e "${GREEN}Gemini API key saved to .env file.${NC}"
  else
    echo -e "${YELLOW}Skipping Gemini API key setup.${NC}"
  fi
else
  echo -e "${GREEN}Gemini API key configuration found.${NC}"
fi

# Ensure agent_memory.yaml exists
if [ ! -f "agent_memory.yaml" ]; then
  echo -e "${YELLOW}agent_memory.yaml not found, creating...${NC}"
  cat > agent_memory.yaml << EOF
index:
  name: "agent_memory"
  prefix: "memory:"
  fields:
    - name: "text_content"
      type: "text"
      weight: 1.0
    - name: "embedding"
      type: "vector"
      attrs:
        dim: 1536
        algorithm: "hnsw"
        distance_metric: "cosine"
        initial_size: 1000
EOF
  echo -e "${GREEN}Created agent_memory.yaml schema file.${NC}"
else
  echo -e "${GREEN}agent_memory.yaml schema file already exists.${NC}"
fi

# Make example script executable
chmod +x redis_semantic_cache_example.py

# Check if Redis is available
echo -e "${YELLOW}Checking Redis connection...${NC}"
if command_exists redis-cli; then
  REDIS_HOST=$(echo $REDIS_URL | sed -E 's|redis://([^@]+@)?([^:]+)(:[0-9]+)?|\2|')
  REDIS_PORT=$(echo $REDIS_URL | sed -E 's|redis://([^@]+@)?[^:]+:([0-9]+)|\2|')
  REDIS_PORT=${REDIS_PORT:-6379}
  
  echo -e "${YELLOW}Testing connection to Redis at ${REDIS_HOST}:${REDIS_PORT}...${NC}"
  if redis-cli -h $REDIS_HOST -p $REDIS_PORT ping > /dev/null 2>&1; then
    echo -e "${GREEN}Redis connection successful!${NC}"
    REDIS_AVAILABLE=1
  else
    echo -e "${YELLOW}Could not connect to Redis. Make sure it's running and accessible.${NC}"
    echo -e "${YELLOW}You can set up Redis using ./setup_redis_for_deployment.sh${NC}"
    REDIS_AVAILABLE=0
  fi
else
  echo -e "${YELLOW}redis-cli not found, skipping connection test.${NC}"
  echo -e "${YELLOW}Install Redis client tools to test the connection.${NC}"
  REDIS_AVAILABLE=0
fi

# Display summary
echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}Redis Semantic Caching setup complete!${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "${YELLOW}To test the semantic cache functionality:${NC}"
echo -e "  ./redis_semantic_cache_example.py"
echo -e ""
echo -e "${YELLOW}To use the semantic cache in your Orchestra application:${NC}"
echo -e "  from redisvl import SemanticCacher"
echo -e "  from langchain_redis.cache import RedisSemanticCache"
echo -e ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Redis URL: ${REDIS_URL}"
echo -e "  Schema file: agent_memory.yaml"
echo -e "${BLUE}======================================================${NC}"

if [ "$REDIS_AVAILABLE" -eq 1 ]; then
  echo -e "${GREEN}Would you like to run the example script now? (y/n)${NC}"
  read -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Running example script...${NC}"
    ./redis_semantic_cache_example.py
  fi
fi

echo -e "${GREEN}Done!${NC}"
