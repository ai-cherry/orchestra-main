# Orchestra AI - Notion Integration Setup Guide

## Overview
This guide provides complete instructions for setting up and using the Orchestra AI Notion integration, which enables seamless synchronization between your AI orchestration system and Notion databases.

## Features

### Current Capabilities
- ✅ Create and update Notion pages programmatically
- ✅ Sync project status and metrics to Notion dashboards
- ✅ Automated daily reports and activity logs
- ✅ Knowledge base management for AI personas
- ✅ Real-time operational insights

### Integration Points
1. **Project Dashboard** - High-level project overview
2. **AI Tools Hub** - Coordination center for all AI services
3. **Persona Knowledge Bases** - Dedicated spaces for Cherry, Sophia, and Karen
4. **Development Activity** - Code commits, deployments, and CI/CD status
5. **Operational Insights** - System health and performance metrics

## Initial Setup

### Step 1: Create Notion Integration
1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Configure:
   - Name: `Orchestra AI System`
   - Associated workspace: Your workspace
   - Capabilities:
     - ✅ Read content
     - ✅ Update content
     - ✅ Insert content
     - ✅ Read comments (optional)

4. Copy the "Internal Integration Token" (starts with `secret_`)

### Step 2: Configure Environment
Add to your environment variables:
```bash
export NOTION_API_KEY="secret_your_token_here"
```

For GitHub Actions, add as repository secret:
- Name: `NOTION_API_KEY`
- Value: Your integration token

### Step 3: Share Databases with Integration
For each Notion database you want to access:
1. Open the database in Notion
2. Click "..." menu → "Add connections"
3. Search for and select "Orchestra AI System"
4. Click "Confirm"

## Database Schemas

### 1. Project Overview Database
**Purpose**: Central project status and metrics

| Property | Type | Description |
|----------|------|-------------|
| Name | Title | Project/Feature name |
| Status | Select | Active, In Progress, Completed, On Hold |
| Priority | Select | Critical, High, Medium, Low |
| Owner | Person | Project lead |
| Due Date | Date | Target completion |
| Progress | Number | 0-100% completion |
| Description | Text | Project details |
| Dependencies | Relation | Links to other projects |
| Metrics | Text | Key performance indicators |

### 2. AI Tools Coordination Hub
**Purpose**: Track and coordinate AI service usage

| Property | Type | Description |
|----------|------|-------------|
| Tool Name | Title | AI service/tool name |
| Provider | Select | OpenAI, Anthropic, DeepSeek, etc. |
| API Key Status | Checkbox | Is configured? |
| Usage This Month | Number | API calls or tokens |
| Cost | Number | Monthly spend |
| Rate Limit | Text | Current limits |
| Last Used | Date | Most recent API call |
| Health Status | Select | Healthy, Warning, Error |
| Notes | Text | Configuration notes |

### 3. Persona Knowledge Bases
**Purpose**: Dedicated knowledge management for each AI persona

#### Cherry (Personal Assistant)
| Property | Type | Description |
|----------|------|-------------|
| Topic | Title | Knowledge topic |
| Category | Multi-select | Calendar, Tasks, Personal, Preferences |
| Content | Text | Detailed information |
| Source | Select | User Input, Learned, System |
| Confidence | Number | 0-100% accuracy |
| Last Updated | Date | When info was updated |
| Access Level | Select | Public, Private, System |

#### Sophia (Financial Advisor)
| Property | Type | Description |
|----------|------|-------------|
| Asset/Topic | Title | Financial instrument or topic |
| Type | Select | Stock, Crypto, Strategy, Market Analysis |
| Current Value | Number | Latest price/value |
| Performance | Number | % change |
| Risk Level | Select | Low, Medium, High |
| Analysis | Text | Expert insights |
| Last Analysis | Date | When analyzed |
| Recommendations | Text | Action items |

#### Karen (Medical Consultant)
| Property | Type | Description |
|----------|------|-------------|
| Medical Topic | Title | Health topic or condition |
| Category | Select | Symptoms, Treatments, Research, Guidelines |
| Evidence Level | Select | High, Moderate, Low |
| Source | URL | Medical reference |
| Summary | Text | Key information |
| Contraindications | Multi-select | Relevant warnings |
| Last Reviewed | Date | Medical review date |
| Professional Notes | Text | Expert annotations |

### 4. Development Activity Log
**Purpose**: Track all development activities

| Property | Type | Description |
|----------|------|-------------|
| Activity | Title | Commit message or action |
| Type | Select | Commit, Deploy, Build, Test, Security |
| Author | Person | Who performed action |
| Repository | Select | Which repo affected |
| Branch | Text | Git branch name |
| Status | Select | Success, Failed, In Progress |
| Timestamp | Date & Time | When it occurred |
| Details | Text | Additional context |
| Link | URL | GitHub/CI link |

### 5. Operational Insights Dashboard
**Purpose**: System health and performance monitoring

| Property | Type | Description |
|----------|------|-------------|
| Metric | Title | What's being measured |
| Category | Select | Performance, Security, Cost, Availability |
| Current Value | Number | Latest measurement |
| Threshold | Number | Alert threshold |
| Status | Select | Normal, Warning, Critical |
| Trend | Select | Improving, Stable, Degrading |
| Last Updated | Date & Time | When measured |
| Action Required | Text | If intervention needed |
| Chart Data | Text | JSON for visualization |

## Code Integration

### Basic Usage
```python
from integrations import get_integration

# Initialize Notion integration
notion = get_integration('notion')

# Create a new page in a database
page_id = notion.create_page(
    parent_database_id="your_database_id",
    properties={
        "Name": {"title": [{"text": {"content": "New Project"}}]},
        "Status": {"select": {"name": "Active"}},
        "Priority": {"select": {"name": "High"}},
        "Progress": {"number": 25}
    }
)
```

### Advanced Examples

#### Update Project Status
```python
def update_project_status(project_name, new_status, progress):
    # This would typically query for the page first
    notion.update_page(
        page_id="existing_page_id",
        properties={
            "Status": {"select": {"name": new_status}},
            "Progress": {"number": progress}
        }
    )
```

#### Log Development Activity
```python
def log_deployment(repo, branch, status, details):
    notion.create_page(
        parent_database_id="dev_activity_db_id",
        properties={
            "Activity": {"title": [{"text": {"content": f"Deploy {repo}"}}]},
            "Type": {"select": {"name": "Deploy"}},
            "Repository": {"select": {"name": repo}},
            "Branch": {"text": {"content": branch}},
            "Status": {"select": {"name": status}},
            "Details": {"rich_text": [{"text": {"content": details}}]}
        }
    )
```

## GitHub Actions Integration

### Daily Notion Report Workflow
The system includes an automated daily report workflow:

```yaml
# .github/workflows/notion-daily-report.yml
name: Daily Notion Report
on:
  schedule:
    - cron: '0 8 * * *'  # 8 AM daily
  workflow_dispatch:

jobs:
  update-notion:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Update Notion Dashboard
        run: python scripts/update_notion_daily.py
        env:
          NOTION_API_KEY: ${{ secrets.NOTION_API_KEY }}
```

## Best Practices

### 1. Rate Limiting
- Notion API has rate limits (3 requests per second)
- Implement exponential backoff for retries
- Batch operations when possible

### 2. Error Handling
```python
try:
    result = notion.create_page(...)
except RuntimeError as e:
    if "rate_limited" in str(e):
        time.sleep(1)
        # Retry
    else:
        # Handle other errors
```

### 3. Data Validation
- Always validate property types match schema
- Use Notion's property format specifications
- Handle missing or null values gracefully

### 4. Security
- Never expose the Notion API key in code
- Use environment variables or secrets management
- Implement proper access controls

## Troubleshooting

### Common Issues

1. **"Unauthorized" Error**
   - Verify API key is correct
   - Ensure integration has access to the database
   - Check workspace permissions

2. **"Database not found"**
   - Confirm database ID is correct
   - Verify integration is connected to database
   - Check if database wasn't deleted

3. **Property type mismatch**
   - Review database schema
   - Ensure property names match exactly (case-sensitive)
   - Verify property value format

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features
1. **Two-way sync** - Pull updates from Notion back to system
2. **Template management** - Create pages from templates
3. **Bulk operations** - Update multiple pages efficiently
4. **Rich media** - Embed charts and visualizations
5. **Comments API** - Add automated comments and mentions

### Integration Expansion
- Connect with Slack for notifications
- Sync with GitHub Issues
- Export to other formats (PDF, Markdown)
- Advanced analytics and reporting

## Support

For issues or questions:
1. Check the [API documentation](https://developers.notion.com)
2. Review error messages and logs
3. Test with the Notion API playground
4. Contact system administrator for access issues

---

Last Updated: December 2024
Version: 1.0
Status: Production Ready 