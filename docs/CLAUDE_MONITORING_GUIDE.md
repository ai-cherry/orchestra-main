# Claude API Monitoring System

Comprehensive monitoring system for tracking Claude API usage, costs, and performance.

## Overview

The Claude API Monitoring System provides real-time tracking and analysis of all Claude API calls made through the cherry_ai-main system. It monitors:

- **Token Usage**: Input and output token counts for each API call
- **Cost Tracking**: Real-time cost calculation based on model pricing
- **Performance Metrics**: Latency measurements and success rates
- **Error Monitoring**: Tracks failures and error patterns
- **Usage Analytics**: Aggregated metrics by model, user, and session

## Architecture

### Components

1. **ClaudeMonitor** (`core/monitoring/claude_monitor.py`)

   - Core monitoring engine
   - Tracks individual API calls
   - Calculates costs based on current pricing
   - Provides aggregated metrics

2. **MonitoredLiteLLMClient** (`core/monitoring/monitored_litellm_client.py`)

   - Extended LiteLLM client with automatic monitoring
   - Transparent integration with existing code
   - Supports all Claude models

3. **Monitoring API** (`core/conductor/src/api/endpoints/monitoring.py`)

   - RESTful API endpoints for accessing metrics
   - Summary statistics and cost breakdowns
   - Data export functionality

4. **Dashboard** (`dashboard/claude-monitoring/index.html`)
   - Real-time web dashboard
   - Interactive charts and metrics
   - Export capabilities

## Setup

### 1. Enable Monitoring

Set the environment variable to use the monitored client:

```bash
export USE_MONITORED_LITELLM=true
export ANTHROPIC_API_KEY="your-api-key"
```

### 2. Configure Storage Backend (Optional)

By default, metrics are stored in memory. For persistent storage:

```bash
# Use Redis
export MONITOR_STORAGE_BACKEND=redis
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Or use MongoDB
export MONITOR_STORAGE_BACKEND=MongoDB
export ```

### 3. Start the API Server

```bash
cd /home/paperspace/cherry_ai-main
python -m core.conductor.src.api.app
```

### 4. Access the Dashboard

Open `http://localhost:8000/dashboard/claude-monitoring/` in your browser.

## Usage

### Basic Monitoring

When `USE_MONITORED_LITELLM=true`, all Claude API calls are automatically monitored:

```python
from core.conductor.src.api.dependencies.llm import get_llm_client

# Get the monitored client
client = get_llm_client()

# Make API calls as usual - monitoring happens automatically
response = await client.chat_completion(
    messages=[{"role": "user", "content": "Hello, Claude!"}],
    model="claude-3-sonnet",
    session_id="user_session_123",
    metadata={"purpose": "greeting"}
)
```

### Programmatic Access

```python
from core.monitoring.monitored_litellm_client import MonitoredLiteLLMClient

# Create a monitored client directly
client = MonitoredLiteLLMClient(
    monitor_all_models=False,  # Only monitor Claude
    api_key_anthropic="your-key"
)

# Get monitoring summary
summary = client.get_monitoring_summary(
    start_time=datetime.now() - timedelta(hours=24),
    model="claude-3-sonnet"
)

print(f"Total cost: ${summary['total_cost_usd']:.2f}")
print(f"Total calls: {summary['total_calls']}")
print(f"Average latency: {summary['average_latency_ms']:.0f}ms")
```

### API Endpoints

#### Get Monitoring Summary

```bash
curl http://localhost:8000/api/monitoring/summary?hours=24
```

#### Get Cost Breakdown

```bash
curl http://localhost:8000/api/monitoring/costs?days=7
```

#### Export Data

```bash
# Export as JSON
curl http://localhost:8000/api/monitoring/export?format=json&hours=24 > metrics.json

# Export as CSV
curl http://localhost:8000/api/monitoring/export?format=csv&hours=24 > metrics.csv
```

## Pricing Information

The system uses current Claude API pricing (as of 2025):

| Model             | Input (per 1M tokens) | Output (per 1M tokens) |
| ----------------- | --------------------- | ---------------------- |
| Claude 3 Opus     | $15.00                | $75.00                 |
| Claude 3 Sonnet   | $3.00                 | $15.00                 |
| Claude 3 Haiku    | $0.25                 | $1.25                  |

## Alerts and Thresholds

### Cost Alerts

Set cost thresholds to receive alerts:

```python
monitor = ClaudeMonitor(
    alert_threshold_cost=10.0  # Alert when session cost exceeds $10
)
```

### Error Alerts

Monitor consecutive errors:

```python
monitor = ClaudeMonitor(
    alert_threshold_errors=5  # Alert after 5 consecutive errors
)
```

## Dashboard Features

### Real-time Metrics

- Total API calls and success rate
- Current costs and token usage
- Average latency

### Interactive Charts

- API calls by model (doughnut chart)
- Cost over time (line chart)
- Token usage by model (stacked bar chart)

### Controls

- Time range selection (1 hour to 1 week)
- Model filtering
- Auto-refresh (30 seconds)

### Export Options

- Download data as JSON or CSV
- Suitable for further analysis in Excel or data tools

## Example: Running the Demo

```bash
# Run the comprehensive demo
cd /home/paperspace/cherry_ai-main
python examples/claude_monitoring_demo.py
```

The demo showcases:

- Basic monitoring setup
- Error handling and alerts
- Cost tracking across sessions
- Data export functionality
- Performance comparisons

## Best Practices

1. **Session Management**: Always provide session IDs to track costs per user/conversation
2. **Metadata**: Use metadata to categorize API calls for better analysis
3. **Regular Exports**: Export data regularly if using in-memory storage
4. **Cost Monitoring**: Set appropriate alert thresholds based on your budget
5. **Performance Tracking**: Monitor latency to identify performance issues

## Troubleshooting

### Monitoring Not Working

1. Ensure `USE_MONITORED_LITELLM=true` is set
2. Check that the API key is valid
3. Verify the monitoring endpoints are registered

### Missing Metrics

1. Check if the model name matches Claude patterns
2. Ensure token usage is being reported by the API
3. Verify the storage backend is accessible

### Dashboard Not Loading

1. Check the API server is running
2. Verify CORS settings allow dashboard access
3. Check browser console for errors

## Integration with Existing Systems

The monitoring system integrates seamlessly with:

- **Logging Infrastructure**: Uses the centralized logging config
- **LiteLLM**: Extends the existing LiteLLM client
- **FastAPI**: Provides RESTful endpoints
- **Memory Systems**: Can store metrics in Redis or MongoDB

## Future Enhancements

- [ ] Grafana integration for advanced dashboards
- [ ] Webhook notifications for alerts
- [ ] Budget management and limits
- [ ] Multi-tenant cost allocation
- [ ] Historical trend analysis
- [ ] A/B testing metrics for different models
