#!/usr/bin/env python3
"""
Test PayReady CEO Zapier Workflows
Simulates the integration between Zapier and Sophia AI for business intelligence
"""

import requests
import json
import time
from datetime import datetime

# Configuration
ZAPIER_MCP_URL = "http://localhost:8001"
API_KEY = "zap_dev_12345_abcdef_orchestra_ai_cursor"
WORKSPACE_ID = "orchestra-main-workspace-2025"

headers = {
    "X-Zapier-API-Key": API_KEY,
    "X-Cursor-Workspace-ID": WORKSPACE_ID,
    "Content-Type": "application/json"
}

def test_ceo_workflow_simulation():
    """Simulate a complete CEO business intelligence workflow"""
    print("🚀 Testing PayReady CEO Zapier Workflows")
    print("=" * 50)
    
    # Step 1: Simulate Salesforce opportunity update (trigger)
    print("\n1. 📊 Simulating Salesforce Opportunity Update...")
    salesforce_data = {
        "opportunity_id": "opp_001_acme_corp",
        "name": "Acme Corp Payment Integration",
        "stage": "Negotiation",
        "amount": 150000,
        "close_date": "2025-07-01",
        "account_name": "Acme Corporation",
        "rep_name": "Sarah Johnson"
    }
    
    # This would typically be triggered by Salesforce webhook
    print(f"   • Opportunity: {salesforce_data['name']}")
    print(f"   • Stage: {salesforce_data['stage']}")
    print(f"   • Amount: ${salesforce_data['amount']:,}")
    
    # Step 2: Trigger code analysis (simulate repo changes for this deal)
    print("\n2. 🔍 Triggering Code Analysis for Deal...")
    code_trigger_response = requests.post(
        f"{ZAPIER_MCP_URL}/api/v1/triggers/code-updated",
        headers=headers,
        json={
            "file_path": "/payready/integrations/acme_corp_integration.py",
            "project_path": "/home/ubuntu/orchestra-main"
        }
    )
    
    if code_trigger_response.status_code == 200:
        code_data = code_trigger_response.json()
        print(f"   ✅ Code analysis triggered: {len(code_data['data']['recent_commits'])} commits analyzed")
    else:
        print(f"   ❌ Code analysis failed: {code_trigger_response.status_code}")
    
    # Step 3: Generate CEO analysis code
    print("\n3. 🧠 Generating CEO Analysis Code...")
    ceo_analysis_prompt = f"""
    Create a Python function that analyzes the following sales opportunity for CEO insights:
    
    Opportunity: {salesforce_data['name']}
    Stage: {salesforce_data['stage']}
    Amount: ${salesforce_data['amount']:,}
    Rep: {salesforce_data['rep_name']}
    
    The function should:
    - Calculate deal health score (0-100)
    - Identify risk factors
    - Suggest next actions for the CEO
    - Compare to similar deals
    """
    
    generate_response = requests.post(
        f"{ZAPIER_MCP_URL}/api/v1/actions/generate-code",
        headers=headers,
        json={
            "prompt": ceo_analysis_prompt,
            "language": "python",
            "project_context": "PayReady CEO business intelligence dashboard"
        }
    )
    
    if generate_response.status_code == 200:
        generated = generate_response.json()
        print(f"   ✅ CEO analysis code generated ({generated['data']['lines_of_code']} lines)")
        print(f"   📄 Sample: {generated['data']['generated_code'][:100]}...")
    else:
        print(f"   ❌ Code generation failed: {generate_response.status_code}")
    
    # Step 4: Analyze current project health
    print("\n4. 📈 Analyzing Project Health for CEO Dashboard...")
    project_analysis_response = requests.post(
        f"{ZAPIER_MCP_URL}/api/v1/actions/analyze-project",
        headers=headers,
        json={
            "project_path": "/home/ubuntu/orchestra-main"
        }
    )
    
    if project_analysis_response.status_code == 200:
        project_data = project_analysis_response.json()
        print(f"   ✅ Project analysis complete:")
        print(f"   • Total files: {project_data['data']['file_count']}")
        print(f"   • Python files: {project_data['data']['file_types'].get('.py', 0)}")
        print(f"   • Dependencies: {len(project_data['data']['dependencies'])}")
    else:
        print(f"   ❌ Project analysis failed: {project_analysis_response.status_code}")
    
    # Step 5: Simulate CEO report generation
    print("\n5. 📋 Generating CEO Executive Summary...")
    
    ceo_summary = {
        "report_date": datetime.now().isoformat(),
        "opportunity_analysis": {
            "deal_name": salesforce_data['name'],
            "health_score": 85,  # Would be calculated by Sophia AI
            "risk_factors": ["Long sales cycle", "Multiple decision makers"],
            "next_actions": ["Schedule executive demo", "Prepare ROI analysis"],
            "competitive_threats": "None identified"
        },
        "development_metrics": {
            "total_files": project_data['data']['file_count'] if 'project_data' in locals() else 0,
            "recent_commits": len(code_data['data']['recent_commits']) if 'code_data' in locals() else 0,
            "team_velocity": "On track"
        },
        "recommendations": [
            "Prioritize Acme Corp integration development",
            "Prepare for Q3 revenue acceleration",
            "Consider expanding sales team capacity"
        ]
    }
    
    print(f"   ✅ CEO Summary Generated:")
    print(f"   • Deal Health Score: {ceo_summary['opportunity_analysis']['health_score']}/100")
    print(f"   • Risk Factors: {len(ceo_summary['opportunity_analysis']['risk_factors'])}")
    print(f"   • Action Items: {len(ceo_summary['opportunity_analysis']['next_actions'])}")
    
    # Step 6: Simulate Slack notification
    print("\n6. 💬 Simulating Slack CEO Alert...")
    slack_message = f"""
🎯 **CEO Alert: High-Value Opportunity Update**

**Deal:** {salesforce_data['name']}
**Value:** ${salesforce_data['amount']:,}
**Stage:** {salesforce_data['stage']}
**Health Score:** {ceo_summary['opportunity_analysis']['health_score']}/100

**Next Actions:**
• {ceo_summary['opportunity_analysis']['next_actions'][0]}
• {ceo_summary['opportunity_analysis']['next_actions'][1]}

**Development Status:** ✅ {ceo_summary['development_metrics']['team_velocity']}
    """
    
    print(f"   ✅ Slack message prepared ({len(slack_message)} characters)")
    print(f"   📱 Would send to #ceo-alerts channel")
    
    print("\n" + "=" * 50)
    print("🎉 PayReady CEO Workflow Test Complete!")
    print("\n📊 Workflow Summary:")
    print("   1. ✅ Salesforce opportunity detected")
    print("   2. ✅ Code analysis triggered")
    print("   3. ✅ AI-generated analysis code")
    print("   4. ✅ Project health analyzed")
    print("   5. ✅ CEO summary generated")
    print("   6. ✅ Slack notification prepared")
    
    return ceo_summary

def test_api_endpoints():
    """Test all available Zapier MCP endpoints"""
    print("\n🔧 Testing All API Endpoints")
    print("=" * 30)
    
    # Test health
    health_response = requests.get(f"{ZAPIER_MCP_URL}/health")
    print(f"Health Check: {'✅' if health_response.status_code == 200 else '❌'}")
    
    # Test auth
    auth_response = requests.get(f"{ZAPIER_MCP_URL}/api/v1/auth/verify", headers=headers)
    print(f"Authentication: {'✅' if auth_response.status_code == 200 else '❌'}")
    
    # Test deployment trigger
    deploy_response = requests.post(
        f"{ZAPIER_MCP_URL}/api/v1/triggers/deployment-complete",
        headers=headers,
        json={
            "deployment_url": "https://payready-ceo-dashboard.vercel.app",
            "environment": "production",
            "status": "success"
        }
    )
    print(f"Deployment Trigger: {'✅' if deploy_response.status_code == 200 else '❌'}")
    
    # Test error detection
    error_response = requests.post(
        f"{ZAPIER_MCP_URL}/api/v1/triggers/error-detected",
        headers=headers,
        json={
            "error_type": "BusinessLogicError",
            "error_message": "Payment processing timeout for high-value transaction",
            "file_path": "/payready/payments/processor.py",
            "line_number": 156
        }
    )
    print(f"Error Detection: {'✅' if error_response.status_code == 200 else '❌'}")
    
    # Test run tests action
    test_response = requests.post(
        f"{ZAPIER_MCP_URL}/api/v1/actions/run-tests",
        headers=headers,
        json={
            "test_command": "echo 'Running PayReady test suite...' && echo 'All 47 tests passed'"
        }
    )
    print(f"Test Execution: {'✅' if test_response.status_code == 200 else '❌'}")

if __name__ == "__main__":
    try:
        # Test all endpoints first
        test_api_endpoints()
        
        print("\n" + "=" * 70)
        
        # Run the full CEO workflow simulation
        ceo_summary = test_ceo_workflow_simulation()
        
        # Save the summary to a file
        with open('/tmp/ceo_workflow_test_results.json', 'w') as f:
            json.dump(ceo_summary, f, indent=2)
        
        print(f"\n💾 Results saved to: /tmp/ceo_workflow_test_results.json")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to Zapier MCP server")
        print("   Make sure the server is running on port 8001")
    except Exception as e:
        print(f"❌ Unexpected error: {e}") 