#!/bin/bash
# monitor_token_usage.sh - Monitor GitHub token usage to prevent rate limiting issues
# This script checks the current rate limit status of your GitHub tokens

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    source .env
    echo "Loaded environment variables from .env file"
fi

# Variables with fallbacks to environment variables
GITHUB_PAT="${GH_CLASSIC_PAT_TOKEN:-${GITHUB_TOKEN:-$(gh auth token)}}"
GITHUB_FINE_GRAINED="${GH_FINE_GRAINED_TOKEN:-""}"
ALERT_THRESHOLD="${RATE_LIMIT_ALERT_THRESHOLD:-20}"  # Alert when remaining rate limit is below this percentage

# Function to check rate limit for a token
check_rate_limit() {
    local token_name=$1
    local token_value=$2
    
    if [ -z "$token_value" ]; then
        echo -e "${YELLOW}No $token_name provided. Skipping.${NC}"
        return
    fi
    
    echo -e "${BLUE}Checking rate limit for $token_name...${NC}"
    
    # Get rate limit information
    local rate_limit_info=$(curl -s -H "Authorization: token $token_value" https://api.github.com/rate_limit)
    
    # Check if the request was successful
    if [[ "$rate_limit_info" == *"Bad credentials"* ]]; then
        echo -e "${RED}Error: Bad credentials for $token_name${NC}"
        return
    fi
    
    # Extract rate limit information
    local remaining=$(echo "$rate_limit_info" | grep -o '"remaining":[0-9]*' | head -1 | cut -d':' -f2)
    local limit=$(echo "$rate_limit_info" | grep -o '"limit":[0-9]*' | head -1 | cut -d':' -f2)
    local reset_timestamp=$(echo "$rate_limit_info" | grep -o '"reset":[0-9]*' | head -1 | cut -d':' -f2)
    
    # Calculate percentage remaining
    local percent=$((remaining * 100 / limit))
    
    # Convert reset timestamp to human-readable format
    local reset_time=$(date -d @"$reset_timestamp" '+%Y-%m-%d %H:%M:%S')
    
    # Display rate limit information
    echo -e "Rate limit for $token_name:"
    echo -e "  Limit: $limit"
    echo -e "  Remaining: $remaining"
    echo -e "  Reset time: $reset_time"
    echo -e "  Percentage remaining: $percent%"
    
    # Check if rate limit is below threshold
    if [ "$percent" -lt "$ALERT_THRESHOLD" ]; then
        echo -e "${RED}WARNING: Rate limit for $token_name is below $ALERT_THRESHOLD% ($percent% remaining)${NC}"
        
        # Send alert (can be extended to send email, Slack notification, etc.)
        if [ -n "$SLACK_WEBHOOK_URL" ]; then
            curl -s -X POST -H 'Content-type: application/json' \
                --data "{\"text\":\"⚠️ GitHub Rate Limit Alert: $token_name is at $percent% ($remaining/$limit) - Resets at $reset_time\"}" \
                "$SLACK_WEBHOOK_URL"
            echo -e "${GREEN}Sent alert to Slack${NC}"
        fi
    else
        echo -e "${GREEN}Rate limit is healthy ($percent% remaining)${NC}"
    fi
    
    echo ""
}

# Check rate limits for both tokens
check_rate_limit "GitHub PAT" "$GITHUB_PAT"
check_rate_limit "GitHub Fine-Grained Token" "$GITHUB_FINE_GRAINED"

# Provide recommendations if rate limits are low
if [ "$percent" -lt "$ALERT_THRESHOLD" ]; then
    echo -e "${YELLOW}Recommendations to avoid rate limiting:${NC}"
    echo "1. Use conditional API requests with If-None-Match header"
    echo "2. Cache API responses when possible"
    echo "3. Use GraphQL API for complex queries to reduce the number of requests"
    echo "4. Implement exponential backoff for retries"
    echo "5. Consider using a different token or waiting until the rate limit resets"
fi

# Add this script to cron to run periodically
if [ "$1" == "--install-cron" ]; then
    echo "Installing cron job to run every hour..."
    (crontab -l 2>/dev/null || echo "") | grep -v "monitor_token_usage.sh" | \
        { cat; echo "0 * * * * $(pwd)/scripts/monitor_token_usage.sh"; } | crontab -
    echo -e "${GREEN}Cron job installed to run every hour${NC}"
fi