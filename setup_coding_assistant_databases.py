#!/usr/bin/env python3
"""
🎯 Enhanced Notion Workspace Setup for Coding Assistant & MCP Integration
Creates specialized databases for AI coding assistance and reflection systems
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Any

def setup_coding_assistant_databases():
    """Create additional databases for coding assistant and MCP integration"""
    
    # Configuration from previous setup
    api_key = "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"
    page_id = "20bdba04940280ca9ba7f9bce721f547"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    print("🎯 Creating Coding Assistant & MCP Integration Databases")
    print("=" * 70)
    
    # Database schemas for coding assistant features
    databases_to_create = [
        {
            "name": "🤖 AI Coding Assistant Rules",
            "description": "Rules, guidelines, and instructions for AI coding assistants",
            "properties": {
                "Rule Name": {"title": {}},
                "Category": {
                    "select": {
                        "options": [
                            {"name": "Code Quality", "color": "blue"},
                            {"name": "Architecture", "color": "green"},
                            {"name": "Security", "color": "red"},
                            {"name": "Performance", "color": "yellow"},
                            {"name": "Documentation", "color": "purple"},
                            {"name": "Testing", "color": "orange"},
                            {"name": "Deployment", "color": "pink"},
                            {"name": "MCP Integration", "color": "gray"}
                        ]
                    }
                },
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "Critical", "color": "red"},
                            {"name": "High", "color": "orange"},
                            {"name": "Medium", "color": "yellow"},
                            {"name": "Low", "color": "gray"}
                        ]
                    }
                },
                "Rule Description": {"rich_text": {}},
                "Code Examples": {"rich_text": {}},
                "Tools Affected": {
                    "multi_select": {
                        "options": [
                            {"name": "Cursor", "color": "blue"},
                            {"name": "Roo Coder", "color": "green"},
                            {"name": "Continue", "color": "purple"},
                            {"name": "GitHub Copilot", "color": "gray"},
                            {"name": "All Tools", "color": "red"}
                        ]
                    }
                },
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Active", "color": "green"},
                            {"name": "Draft", "color": "yellow"},
                            {"name": "Deprecated", "color": "red"},
                            {"name": "Under Review", "color": "orange"}
                        ]
                    }
                },
                "Last Updated": {"date": {}},
                "Created By": {"rich_text": {}},
                "Related MCP": {"rich_text": {}}
            }
        },
        {
            "name": "🔗 MCP Connections & Context",
            "description": "Model Context Protocol connections and contextual memory management",
            "properties": {
                "Connection Name": {"title": {}},
                "MCP Type": {
                    "select": {
                        "options": [
                            {"name": "File System", "color": "blue"},
                            {"name": "Database", "color": "green"},
                            {"name": "API Service", "color": "purple"},
                            {"name": "Memory Store", "color": "orange"},
                            {"name": "Tool Integration", "color": "red"},
                            {"name": "Context Provider", "color": "yellow"}
                        ]
                    }
                },
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Active", "color": "green"},
                            {"name": "Inactive", "color": "red"},
                            {"name": "Testing", "color": "yellow"},
                            {"name": "Error", "color": "red"},
                            {"name": "Maintenance", "color": "orange"}
                        ]
                    }
                },
                "Configuration": {"rich_text": {}},
                "Context Scope": {
                    "multi_select": {
                        "options": [
                            {"name": "Project-wide", "color": "blue"},
                            {"name": "File-specific", "color": "green"},
                            {"name": "Function-level", "color": "purple"},
                            {"name": "Global", "color": "red"},
                            {"name": "Session-based", "color": "yellow"}
                        ]
                    }
                },
                "Memory Retention": {
                    "select": {
                        "options": [
                            {"name": "Permanent", "color": "green"},
                            {"name": "Session", "color": "yellow"},
                            {"name": "Temporary", "color": "orange"},
                            {"name": "Cache", "color": "gray"}
                        ]
                    }
                },
                "Connected Tools": {
                    "multi_select": {
                        "options": [
                            {"name": "Cursor", "color": "blue"},
                            {"name": "Roo Coder", "color": "green"},
                            {"name": "Continue", "color": "purple"},
                            {"name": "Orchestra AI", "color": "red"}
                        ]
                    }
                },
                "Last Sync": {"date": {}},
                "Performance Metrics": {"rich_text": {}},
                "Error Log": {"rich_text": {}}
            }
        },
        {
            "name": "🔄 Code Reflection System",
            "description": "Reflection and learning system for code improvements and patterns",
            "properties": {
                "Reflection Title": {"title": {}},
                "Reflection Type": {
                    "select": {
                        "options": [
                            {"name": "Code Review", "color": "blue"},
                            {"name": "Architecture Decision", "color": "green"},
                            {"name": "Performance Analysis", "color": "yellow"},
                            {"name": "Bug Analysis", "color": "red"},
                            {"name": "Pattern Recognition", "color": "purple"},
                            {"name": "Tool Effectiveness", "color": "orange"},
                            {"name": "Learning Insight", "color": "pink"}
                        ]
                    }
                },
                "Trigger Event": {
                    "select": {
                        "options": [
                            {"name": "Code Completion", "color": "green"},
                            {"name": "Error Encountered", "color": "red"},
                            {"name": "Performance Issue", "color": "yellow"},
                            {"name": "Manual Review", "color": "blue"},
                            {"name": "Automated Analysis", "color": "purple"},
                            {"name": "User Feedback", "color": "orange"}
                        ]
                    }
                },
                "Code Context": {"rich_text": {}},
                "Analysis": {"rich_text": {}},
                "Lessons Learned": {"rich_text": {}},
                "Action Items": {"rich_text": {}},
                "Confidence Score": {
                    "select": {
                        "options": [
                            {"name": "High", "color": "green"},
                            {"name": "Medium", "color": "yellow"},
                            {"name": "Low", "color": "red"},
                            {"name": "Uncertain", "color": "gray"}
                        ]
                    }
                },
                "Impact Level": {
                    "select": {
                        "options": [
                            {"name": "Critical", "color": "red"},
                            {"name": "High", "color": "orange"},
                            {"name": "Medium", "color": "yellow"},
                            {"name": "Low", "color": "gray"}
                        ]
                    }
                },
                "Related Files": {"rich_text": {}},
                "Tool Used": {
                    "select": {
                        "options": [
                            {"name": "Cursor", "color": "blue"},
                            {"name": "Roo Coder", "color": "green"},
                            {"name": "Continue", "color": "purple"},
                            {"name": "Manual Analysis", "color": "gray"},
                            {"name": "Automated Tool", "color": "orange"}
                        ]
                    }
                },
                "Follow-up Required": {"checkbox": {}},
                "Date Created": {"date": {}},
                "Resolution Status": {
                    "select": {
                        "options": [
                            {"name": "Resolved", "color": "green"},
                            {"name": "In Progress", "color": "yellow"},
                            {"name": "Pending", "color": "orange"},
                            {"name": "Blocked", "color": "red"}
                        ]
                    }
                }
            }
        },
        {
            "name": "📊 AI Tool Performance Metrics",
            "description": "Performance tracking and optimization for AI coding tools",
            "properties": {
                "Metric Name": {"title": {}},
                "Tool": {
                    "select": {
                        "options": [
                            {"name": "Cursor", "color": "blue"},
                            {"name": "Roo Coder", "color": "green"},
                            {"name": "Continue", "color": "purple"},
                            {"name": "Orchestra AI", "color": "red"},
                            {"name": "GitHub Copilot", "color": "gray"},
                            {"name": "Combined", "color": "orange"}
                        ]
                    }
                },
                "Metric Type": {
                    "select": {
                        "options": [
                            {"name": "Response Time", "color": "yellow"},
                            {"name": "Accuracy", "color": "green"},
                            {"name": "Code Quality", "color": "blue"},
                            {"name": "User Satisfaction", "color": "purple"},
                            {"name": "Error Rate", "color": "red"},
                            {"name": "Usage Frequency", "color": "orange"}
                        ]
                    }
                },
                "Current Value": {"number": {}},
                "Target Value": {"number": {}},
                "Trend": {
                    "select": {
                        "options": [
                            {"name": "Improving", "color": "green"},
                            {"name": "Stable", "color": "yellow"},
                            {"name": "Declining", "color": "red"},
                            {"name": "Fluctuating", "color": "orange"}
                        ]
                    }
                },
                "Measurement Period": {"rich_text": {}},
                "Data Source": {"rich_text": {}},
                "Notes": {"rich_text": {}},
                "Last Updated": {"date": {}},
                "Alert Threshold": {"number": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Normal", "color": "green"},
                            {"name": "Warning", "color": "yellow"},
                            {"name": "Critical", "color": "red"},
                            {"name": "Unknown", "color": "gray"}
                        ]
                    }
                }
            }
        }
    ]
    
    created_databases = {}
    
    # Create each database
    for db_config in databases_to_create:
        print(f"Creating: {db_config['name']}")
        
        database_data = {
            "parent": {"page_id": page_id},
            "title": [{"text": {"content": db_config['name']}}],
            "properties": db_config['properties']
        }
        
        try:
            response = requests.post(
                "https://api.notion.com/v1/databases",
                headers=headers,
                json=database_data
            )
            
            if response.status_code == 200:
                db_info = response.json()
                created_databases[db_config['name']] = db_info['id']
                print(f"✅ Created: {db_config['name']} (ID: {db_info['id'][:8]}...)")
            else:
                print(f"❌ Failed to create {db_config['name']}: {response.text}")
                
        except Exception as e:
            print(f"❌ Error creating {db_config['name']}: {str(e)}")
    
    # Add sample data to the new databases
    print("\n📝 Adding sample data...")
    
    # Sample AI Coding Rules
    if "🤖 AI Coding Assistant Rules" in created_databases:
        sample_rules = [
            {
                "Rule Name": {"title": [{"text": {"content": "Always Use Type Hints"}}]},
                "Category": {"select": {"name": "Code Quality"}},
                "Priority": {"select": {"name": "High"}},
                "Rule Description": {"rich_text": [{"text": {"content": "All Python functions and methods must include proper type hints for parameters and return values to improve code readability and IDE support."}}]},
                "Code Examples": {"rich_text": [{"text": {"content": "def process_data(items: List[Dict[str, Any]]) -> Dict[str, int]:\n    return {'count': len(items)}"}}]},
                "Tools Affected": {"multi_select": [{"name": "All Tools"}]},
                "Status": {"select": {"name": "Active"}},
                "Last Updated": {"date": {"start": datetime.now().isoformat()}},
                "Created By": {"rich_text": [{"text": {"content": "Orchestra AI Setup"}}]}
            },
            {
                "Rule Name": {"title": [{"text": {"content": "MCP Context Preservation"}}]},
                "Category": {"select": {"name": "MCP Integration"}},
                "Priority": {"select": {"name": "Critical"}},
                "Rule Description": {"rich_text": [{"text": {"content": "When using MCP connections, always preserve context between sessions and maintain connection state for optimal performance."}}]},
                "Tools Affected": {"multi_select": [{"name": "Cursor"}, {"name": "Continue"}]},
                "Status": {"select": {"name": "Active"}},
                "Last Updated": {"date": {"start": datetime.now().isoformat()}},
                "Created By": {"rich_text": [{"text": {"content": "Orchestra AI Setup"}}]}
            },
            {
                "Rule Name": {"title": [{"text": {"content": "Security-First Development"}}]},
                "Category": {"select": {"name": "Security"}},
                "Priority": {"select": {"name": "Critical"}},
                "Rule Description": {"rich_text": [{"text": {"content": "Never hardcode API keys, passwords, or sensitive data. Always use environment variables or secure configuration management."}}]},
                "Code Examples": {"rich_text": [{"text": {"content": "# Good\napi_key = os.getenv('API_KEY')\n\n# Bad\napi_key = 'sk-1234567890abcdef'"}}]},
                "Tools Affected": {"multi_select": [{"name": "All Tools"}]},
                "Status": {"select": {"name": "Active"}},
                "Last Updated": {"date": {"start": datetime.now().isoformat()}},
                "Created By": {"rich_text": [{"text": {"content": "Orchestra AI Setup"}}]}
            }
        ]
        
        for rule in sample_rules:
            try:
                response = requests.post(
                    "https://api.notion.com/v1/pages",
                    headers=headers,
                    json={
                        "parent": {"database_id": created_databases["🤖 AI Coding Assistant Rules"]},
                        "properties": rule
                    }
                )
                if response.status_code == 200:
                    print(f"✅ Added rule: {rule['Rule Name']['title'][0]['text']['content']}")
            except Exception as e:
                print(f"❌ Error adding rule: {str(e)}")
    
    # Sample MCP Connections
    if "🔗 MCP Connections & Context" in created_databases:
        sample_connections = [
            {
                "Connection Name": {"title": [{"text": {"content": "Orchestra File System MCP"}}]},
                "MCP Type": {"select": {"name": "File System"}},
                "Status": {"select": {"name": "Active"}},
                "Configuration": {"rich_text": [{"text": {"content": "{\n  \"root_path\": \"/tmp/orchestra-main\",\n  \"allowed_extensions\": [\".py\", \".ts\", \".tsx\", \".md\"],\n  \"max_file_size\": \"10MB\"\n}"}}]},
                "Context Scope": {"multi_select": [{"name": "Project-wide"}]},
                "Memory Retention": {"select": {"name": "Session"}},
                "Connected Tools": {"multi_select": [{"name": "Cursor"}, {"name": "Continue"}]},
                "Last Sync": {"date": {"start": datetime.now().isoformat()}}
            },
            {
                "Connection Name": {"title": [{"text": {"content": "Notion API Context Provider"}}]},
                "MCP Type": {"select": {"name": "API Service"}},
                "Status": {"select": {"name": "Active"}},
                "Configuration": {"rich_text": [{"text": {"content": "{\n  \"api_endpoint\": \"https://api.notion.com/v1\",\n  \"workspace_id\": \"20bdba04940280ca9ba7f9bce721f547\",\n  \"cache_duration\": \"15m\"\n}"}}]},
                "Context Scope": {"multi_select": [{"name": "Global"}]},
                "Memory Retention": {"select": {"name": "Permanent"}},
                "Connected Tools": {"multi_select": [{"name": "Orchestra AI"}]},
                "Last Sync": {"date": {"start": datetime.now().isoformat()}}
            }
        ]
        
        for connection in sample_connections:
            try:
                response = requests.post(
                    "https://api.notion.com/v1/pages",
                    headers=headers,
                    json={
                        "parent": {"database_id": created_databases["🔗 MCP Connections & Context"]},
                        "properties": connection
                    }
                )
                if response.status_code == 200:
                    print(f"✅ Added MCP connection: {connection['Connection Name']['title'][0]['text']['content']}")
            except Exception as e:
                print(f"❌ Error adding MCP connection: {str(e)}")
    
    # Update root page with new database links
    print("\n🔗 Updating root page with new databases...")
    
    try:
        # Get current page content
        page_response = requests.get(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=headers
        )
        
        if page_response.status_code == 200:
            # Add new section to page
            new_content = {
                "children": [
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"text": {"content": "🤖 AI Coding Assistant & MCP Integration"}}]
                        }
                    },
                    {
                        "object": "block", 
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": "Advanced databases for AI coding assistance, MCP integration, and reflection systems."}}]
                        }
                    }
                ]
            }
            
            # Add database links
            for db_name, db_id in created_databases.items():
                new_content["children"].append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"text": {"content": f"• {db_name}: "}},
                            {
                                "text": {"content": f"https://notion.so/{db_id.replace('-', '')}"},
                                "href": f"https://notion.so/{db_id.replace('-', '')}"
                            }
                        ]
                    }
                })
            
            # Append to page
            append_response = requests.patch(
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                headers=headers,
                json=new_content
            )
            
            if append_response.status_code == 200:
                print("✅ Updated root page with new database links")
            else:
                print(f"❌ Failed to update root page: {append_response.text}")
                
    except Exception as e:
        print(f"❌ Error updating root page: {str(e)}")
    
    # Save configuration
    config = {
        "setup_date": datetime.now().isoformat(),
        "setup_version": "3.0 - Coding Assistant & MCP Integration",
        "new_databases": created_databases,
        "total_databases": len(created_databases)
    }
    
    with open("/tmp/orchestra-main/coding_assistant_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("\n" + "=" * 70)
    print("🎉 CODING ASSISTANT & MCP DATABASES SETUP COMPLETE!")
    print("=" * 70)
    print(f"✅ Created {len(created_databases)} new databases")
    print("✅ Added sample data and configurations")
    print("✅ Updated root page with database links")
    print("✅ Configuration saved to coding_assistant_config.json")
    print("\n🔗 New Database URLs:")
    for db_name, db_id in created_databases.items():
        print(f"   • {db_name}: https://notion.so/{db_id.replace('-', '')}")
    
    return created_databases

if __name__ == "__main__":
    setup_coding_assistant_databases()

