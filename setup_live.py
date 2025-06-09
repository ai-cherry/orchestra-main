#!/usr/bin/env python3
"""
🎯 Orchestra AI Notion Workspace Setup - LIVE EXECUTION
Using exact credentials from user screenshots
"""

import requests
import json
import sys
from datetime import datetime

def setup_workspace_live():
    """Setup workspace with exact credentials from screenshots"""
    
    # Exact credentials from user screenshots
    page_id = "20bdba04940280ca9ba7f9bce721f547"
    api_key = "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"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    base_url = "https://api.notion.com/v1"
    session = requests.Session()
    session.headers.update(headers)
    
    print("🏢 Orchestra AI Notion Workspace Setup - LIVE EXECUTION")
    print("=" * 70)
    print(f"📄 Page ID: {page_id}")
    print(f"🔑 API Token: {api_key[:15]}...{api_key[-4:]}")
    print(f"🔗 Page URL: https://www.notion.so/Orchestra-AI-Workspace-{page_id}")
    print()
    
    # Verify page exists and is accessible
    print("1️⃣ Verifying page access...")
    try:
        response = session.get(f"{base_url}/pages/{page_id}")
        if response.status_code != 200:
            print(f"❌ Cannot access page. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        print("✅ Page access verified - Integration has proper permissions")
        page_data = response.json()
        print(f"   Page title: {page_data.get('properties', {}).get('title', {}).get('title', [{}])[0].get('text', {}).get('content', 'Orchestra AI Workspace')}")
    except Exception as e:
        print(f"❌ Error accessing page: {e}")
        return False
    
    # Create databases with comprehensive schemas
    databases = {}
    database_configs = [
        ("🎯 Epic & Feature Tracking", get_epic_schema()),
        ("📋 Task Management", get_task_schema()),
        ("💻 Development Log", get_dev_log_schema()),
        ("🍒 Cherry Features", get_cherry_schema()),
        ("👩‍💼 Sophia Features", get_sophia_schema()),
        ("👩‍⚕️ Karen Features", get_karen_schema()),
        ("📖 Patrick Instructions", get_patrick_schema()),
        ("📚 Knowledge Base", get_knowledge_schema())
    ]
    
    print("2️⃣ Creating Orchestra AI databases...")
    for i, (db_name, db_schema) in enumerate(database_configs, 1):
        try:
            print(f"   Creating {i}/8: {db_name}")
            
            database_data = {
                "parent": {"type": "page_id", "page_id": page_id},
                "title": [{"text": {"content": db_name}}],
                "properties": db_schema
            }
            
            response = session.post(f"{base_url}/databases", json=database_data)
            if response.status_code == 200:
                db_id = response.json()["id"]
                databases[db_name] = db_id
                print(f"   ✅ Created: {db_name} (ID: {db_id[:8]}...)")
            else:
                print(f"   ❌ Failed: {db_name}")
                print(f"      Status: {response.status_code}")
                print(f"      Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error creating {db_name}: {e}")
    
    if not databases:
        print("❌ No databases were created. Check permissions and try again.")
        return False
    
    print(f"✅ Successfully created {len(databases)} databases!")
    
    # Add sample data to demonstrate functionality
    print("3️⃣ Adding sample data and Patrick Instructions...")
    
    # Add sample tasks
    if "📋 Task Management" in databases:
        try:
            sample_tasks = [
                {
                    "title": "✅ Notion Integration Complete",
                    "status": "Done",
                    "type": "Infrastructure",
                    "priority": "High",
                    "assignee": "Human Developer",
                    "tool": "Manual",
                    "description": "Successfully set up complete Notion workspace with 8 databases for Orchestra AI project management and automation."
                },
                {
                    "title": "Implement GitHub Webhooks",
                    "status": "Ready",
                    "type": "Feature",
                    "priority": "High",
                    "assignee": "Sophia",
                    "tool": "Cursor",
                    "description": "Set up automatic task creation from GitHub issues and pull requests using Notion webhooks."
                },
                {
                    "title": "Lambda Labs Cost Monitoring",
                    "status": "In Progress",
                    "type": "Infrastructure",
                    "priority": "Medium",
                    "assignee": "Karen",
                    "tool": " Coder",
                    "description": "Implement automated monitoring and alerts for Lambda Labs GPU usage and costs."
                }
            ]
            
            for task in sample_tasks:
                task_data = {
                    "parent": {"database_id": databases["📋 Task Management"]},
                    "properties": {
                        "Title": {"title": [{"text": {"content": task["title"]}}]},
                        "Status": {"select": {"name": task["status"]}},
                        "Type": {"select": {"name": task["type"]}},
                        "Priority": {"select": {"name": task["priority"]}},
                        "Assignee": {"select": {"name": task["assignee"]}},
                        "Development Tool": {"select": {"name": task["tool"]}},
                        "Description": {"rich_text": [{"text": {"content": task["description"]}}]}
                    }
                }
                
                response = session.post(f"{base_url}/pages", json=task_data)
                if response.status_code == 200:
                    print(f"   ✅ Added task: {task['title']}")
                else:
                    print(f"   ⚠️ Could not add task: {task['title']}")
        except Exception as e:
            print(f"   ⚠️ Could not add sample tasks: {e}")
    
    # Add comprehensive Patrick Instructions
    if "📖 Patrick Instructions" in databases:
        try:
            instructions = [
                {
                    "title": "Daily System Health Check",
                    "category": "Daily Operations",
                    "priority": "P1 - High Impact",
                    "frequency": "Daily",
                    "automation": "Script Assisted",
                    "risk": "Medium",
                    "commands": """# Daily System Health Check - Orchestra AI
1. Check Lambda Labs GPU utilization: `nvidia-smi`
2. Verify GitHub Actions status: Visit repository Actions tab
3. Review Notion API rate limits: Check integration usage
4. Monitor application logs: `tail -f /var/log/orchestra.log`
5. Validate backup completion: Check backup timestamps
6. Test AI agent responsiveness: Run health check endpoints
7. Review cost metrics: Check Lambda Labs billing dashboard""",
                    "prerequisites": "Access to Lambda Labs dashboard, GitHub repository, server logs",
                    "expected_output": "All systems green, no critical alerts, costs within budget"
                },
                {
                    "title": "Emergency System Recovery",
                    "category": "Emergency Procedures",
                    "priority": "P0 - System Critical",
                    "frequency": "As Needed",
                    "automation": "Fully Manual",
                    "risk": "Critical",
                    "commands": """# Emergency System Recovery - Orchestra AI
1. Assess system status and identify failure point
2. Check recent deployments and configuration changes
3. Review error logs and monitoring alerts
4. Rollback to last known good state if possible
5. Restore from backup if system corruption detected
6. Notify stakeholders immediately via all channels
7. Document incident in detail for post-mortem
8. Conduct post-incident review and update procedures""",
                    "prerequisites": "Emergency access credentials, backup access, stakeholder contact list",
                    "expected_output": "System restored, stakeholders notified, incident documented"
                },
                {
                    "title": "AI Agent Performance Optimization",
                    "category": "Weekly Maintenance",
                    "priority": "P1 - High Impact",
                    "frequency": "Weekly",
                    "automation": "AI Assisted",
                    "risk": "Low",
                    "commands": """# AI Agent Performance Optimization
1. Review Cherry, Sophia, Karen performance metrics
2. Analyze response times and accuracy rates
3. Check for model drift or degradation
4. Update prompts and fine-tuning if needed
5. Test cross-agent collaboration workflows
6. Optimize resource allocation and costs
7. Update performance baselines""",
                    "prerequisites": "AI performance monitoring tools, model access",
                    "expected_output": "Optimized performance, updated baselines, cost efficiency improved"
                }
            ]
            
            for instruction in instructions:
                instruction_data = {
                    "parent": {"database_id": databases["📖 Patrick Instructions"]},
                    "properties": {
                        "Instruction Title": {"title": [{"text": {"content": instruction["title"]}}]},
                        "Category": {"select": {"name": instruction["category"]}},
                        "Priority Level": {"select": {"name": instruction["priority"]}},
                        "Frequency": {"select": {"name": instruction["frequency"]}},
                        "Automation Level": {"select": {"name": instruction["automation"]}},
                        "Risk Level": {"select": {"name": instruction["risk"]}},
                        "Command Sequence": {"rich_text": [{"text": {"content": instruction["commands"]}}]},
                        "Prerequisites": {"rich_text": [{"text": {"content": instruction["prerequisites"]}}]},
                        "Expected Output": {"rich_text": [{"text": {"content": instruction["expected_output"]}}]}
                    }
                }
                
                response = session.post(f"{base_url}/pages", json=instruction_data)
                if response.status_code == 200:
                    print(f"   ✅ Added: {instruction['title']}")
                else:
                    print(f"   ⚠️ Could not add: {instruction['title']}")
        except Exception as e:
            print(f"   ⚠️ Could not add Patrick Instructions: {e}")
    
    try:
        # Create page content with database links
        page_blocks = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"text": {"content": "🎉 Orchestra AI Workspace - Setup Complete!"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": f"Workspace successfully set up on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}. All {len(databases)} databases are ready for use with comprehensive schemas and sample data."}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "📊 Project Databases"}}]}
            }
        ]
        
        # Add database links
        for db_name, db_id in databases.items():
            clean_db_id = db_id.replace('-', '')
            page_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": f"• {db_name}: "}},
                        {
                            "text": {"content": "Open Database", "link": {"url": f"https://notion.so/{clean_db_id}"}},
                            "annotations": {"bold": True, "color": "blue"}
                        }
                    ]
                }
            })
        
        # Add next steps
        page_blocks.extend([
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "🚀 Next Steps"}}]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": "Explore each database to see the comprehensive structure and sample data"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": "Review the Patrick Instructions for critical operational procedures"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": "Set up GitHub webhooks for automatic task creation"}}]
                }
            }
        ])
        
        # Add blocks to the page
        response = session.patch(
            f"{base_url}/blocks/{page_id}/children",
            json={"children": page_blocks}
        )
        
        if response.status_code == 200:
            print("   ✅ t page updated with database links and setup information")
        else:
            
    except Exception as e:
    
    # Save configuration
    config = {
        "setup_date": datetime.now().isoformat(),
        "setup_version": "2.0 - Live Execution",
        "api_token": api_key,
        "databases": databases,
        "databases_created": len(databases),
        "database_urls": {name: f"https://notion.so/{db_id.replace('-', '')}" for name, db_id in databases.items()}
    }
    
    with open("orchestra_notion_config_live.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("\n" + "="*80)
    print("🎉 ORCHESTRA AI NOTION WORKSPACE SETUP COMPLETE!")
    print("="*80)
    print(f"✅ t Page: https://www.notion.so/Orchestra-AI-Workspace-{page_id}")
    print(f"✅ Databases Created: {len(databases)}")
    print(f"✅ Configuration Saved: orchestra_notion_config_live.json")
    print()
    print("📊 Created Databases:")
    for db_name, db_id in databases.items():
        clean_id = db_id.replace('-', '')
        print(f"   • {db_name}")
        print(f"     URL: https://notion.so/{clean_id}")
    print()
    print("🎯 Your Orchestra AI workspace is now fully operational!")
    print("   Refresh your Notion page to see all the new databases and features.")
    
    return True

# Database schemas (same as before but optimized)
def get_epic_schema():
    return {
        "Title": {"title": {}},
        "Status": {
            "select": {
                "options": [
                    {"name": "Planning", "color": "gray"},
                    {"name": "In Progress", "color": "blue"},
                    {"name": "Review", "color": "yellow"},
                    {"name": "Done", "color": "green"},
                    {"name": "Blocked", "color": "red"}
                ]
            }
        },
        "Priority": {
            "select": {
                "options": [
                    {"name": "P0 - Critical", "color": "red"},
                    {"name": "P1 - High", "color": "orange"},
                    {"name": "P2 - Medium", "color": "yellow"},
                    {"name": "P3 - Low", "color": "gray"}
                ]
            }
        },
        "Assigned Persona": {
            "multi_select": {
                "options": [
                    {"name": "Cherry", "color": "red"},
                    {"name": "Sophia", "color": "blue"},
                    {"name": "Karen", "color": "green"},
                    {"name": "Human Team", "color": "purple"}
                ]
            }
        },
        "Story Points": {"number": {"format": "number"}},
        "Created": {"created_time": {}}
    }

def get_task_schema():
    return {
        "Title": {"title": {}},
        "Status": {
            "select": {
                "options": [
                    {"name": "Backlog", "color": "gray"},
                    {"name": "Ready", "color": "blue"},
                    {"name": "In Progress", "color": "yellow"},
                    {"name": "Done", "color": "green"},
                    {"name": "Blocked", "color": "red"}
                ]
            }
        },
        "Type": {
            "select": {
                "options": [
                    {"name": "Feature", "color": "green"},
                    {"name": "Bug Fix", "color": "red"},
                    {"name": "Infrastructure", "color": "gray"},
                    {"name": "Research", "color": "blue"}
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
        "Assignee": {
            "select": {
                "options": [
                    {"name": "Cherry", "color": "red"},
                    {"name": "Sophia", "color": "blue"},
                    {"name": "Karen", "color": "green"},
                    {"name": "Human Developer", "color": "purple"}
                ]
            }
        },
        "Development Tool": {
            "select": {
                "options": [
                    {"name": "Cursor", "color": "blue"},
                    {"name": " Coder", "color": "green"},
                    {"name": "Continue", "color": "purple"},
                    {"name": "Manual", "color": "gray"}
                ]
            }
        },
        "Description": {"rich_text": {}},
        "Created": {"created_time": {}}
    }

def get_dev_log_schema():
    return {
        "Title": {"title": {}},
        "Date": {"date": {}},
        "Type": {
            "select": {
                "options": [
                    {"name": "Code", "color": "blue"},
                    {"name": "UI", "color": "pink"},
                    {"name": "Bug Fix", "color": "red"},
                    {"name": "Feature", "color": "green"}
                ]
            }
        },
        "Tool Used": {
            "select": {
                "options": [
                    {"name": "Cursor", "color": "blue"},
                    {"name": "", "color": "green"},
                    {"name": "Continue", "color": "purple"},
                    {"name": "Manual", "color": "gray"}
                ]
            }
        },
        "Notes": {"rich_text": {}},
        "Created": {"created_time": {}}
    }

def get_cherry_schema():
    return {
        "Feature Name": {"title": {}},
        "Category": {
            "select": {
                "options": [
                    {"name": "Wellness Coaching", "color": "green"},
                    {"name": "Travel Planning", "color": "blue"},
                    {"name": "Creative Collaboration", "color": "purple"},
                    {"name": "Personal Assistant", "color": "red"}
                ]
            }
        },
        "Development Status": {
            "select": {
                "options": [
                    {"name": "Concept", "color": "gray"},
                    {"name": "Prototype", "color": "yellow"},
                    {"name": "Beta", "color": "orange"},
                    {"name": "Production", "color": "green"}
                ]
            }
        },
        "User Stories": {"rich_text": {}},
        "Created": {"created_time": {}}
    }

def get_sophia_schema():
    return {
        "Feature Name": {"title": {}},
        "Business Domain": {
            "select": {
                "options": [
                    {"name": "Market Analysis", "color": "blue"},
                    {"name": "Revenue Optimization", "color": "green"},
                    {"name": "Strategic Planning", "color": "purple"},
                    {"name": "Financial Analytics", "color": "red"}
                ]
            }
        },
        "Business Impact": {
            "select": {
                "options": [
                    {"name": "High", "color": "green"},
                    {"name": "Medium", "color": "yellow"},
                    {"name": "Low", "color": "gray"}
                ]
            }
        },
        "Business Requirements": {"rich_text": {}},
        "Created": {"created_time": {}}
    }

def get_karen_schema():
    return {
        "Feature Name": {"title": {}},
        "Healthcare Domain": {
            "select": {
                "options": [
                    {"name": "Clinical Research", "color": "blue"},
                    {"name": "Patient Care", "color": "green"},
                    {"name": "Medical Knowledge", "color": "purple"},
                    {"name": "Compliance", "color": "red"}
                ]
            }
        },
        "Patient Safety Impact": {
            "select": {
                "options": [
                    {"name": "Critical", "color": "red"},
                    {"name": "High", "color": "orange"},
                    {"name": "Medium", "color": "yellow"},
                    {"name": "Low", "color": "green"}
                ]
            }
        },
        "Clinical Requirements": {"rich_text": {}},
        "Created": {"created_time": {}}
    }

def get_patrick_schema():
    return {
        "Instruction Title": {"title": {}},
        "Category": {
            "select": {
                "options": [
                    {"name": "Daily Operations", "color": "blue"},
                    {"name": "Emergency Procedures", "color": "red"},
                    {"name": "Weekly Maintenance", "color": "green"},
                    {"name": "Monthly Reviews", "color": "orange"}
                ]
            }
        },
        "Priority Level": {
            "select": {
                "options": [
                    {"name": "P0 - System Critical", "color": "red"},
                    {"name": "P1 - High Impact", "color": "orange"},
                    {"name": "P2 - Medium Impact", "color": "yellow"},
                    {"name": "P3 - Low Impact", "color": "gray"}
                ]
            }
        },
        "Frequency": {
            "select": {
                "options": [
                    {"name": "Daily", "color": "blue"},
                    {"name": "Weekly", "color": "green"},
                    {"name": "Monthly", "color": "orange"},
                    {"name": "As Needed", "color": "gray"}
                ]
            }
        },
        "Automation Level": {
            "select": {
                "options": [
                    {"name": "Fully Manual", "color": "red"},
                    {"name": "Script Assisted", "color": "orange"},
                    {"name": "Semi-Automated", "color": "yellow"},
                    {"name": "AI Assisted", "color": "blue"}
                ]
            }
        },
        "Risk Level": {
            "select": {
                "options": [
                    {"name": "Low", "color": "green"},
                    {"name": "Medium", "color": "yellow"},
                    {"name": "High", "color": "orange"},
                    {"name": "Critical", "color": "red"}
                ]
            }
        },
        "Command Sequence": {"rich_text": {}},
        "Prerequisites": {"rich_text": {}},
        "Expected Output": {"rich_text": {}},
        "Created": {"created_time": {}}
    }

def get_knowledge_schema():
    return {
        "Knowledge Item": {"title": {}},
        "Knowledge Type": {
            "select": {
                "options": [
                    {"name": "Best Practice", "color": "green"},
                    {"name": "Lesson Learned", "color": "orange"},
                    {"name": "Troubleshooting", "color": "red"},
                    {"name": "Configuration", "color": "blue"}
                ]
            }
        },
        "Complexity Level": {
            "select": {
                "options": [
                    {"name": "Basic", "color": "green"},
                    {"name": "Intermediate", "color": "yellow"},
                    {"name": "Advanced", "color": "orange"},
                    {"name": "Expert", "color": "red"}
                ]
            }
        },
        "Detailed Content": {"rich_text": {}},
        "Created": {"created_time": {}}
    }

def main():
    """Main setup function"""
    try:
        success = setup_workspace_live()
        
        if success:
            print("\n🎉 SETUP COMPLETED SUCCESSFULLY!")
            print("🔄 Refresh your Notion page to see all the new databases!")
            return 0
        else:
            print("\n❌ Setup failed. Please check the errors above.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

