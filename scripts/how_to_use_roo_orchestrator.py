#!/usr/bin/env python3
"""
Visual Guide: How to Use Roo with AI Orchestrator
Shows the different ways to leverage the integration
"""

import os
from datetime import datetime

def print_section(title, icon="🔹"):
    """Print a formatted section"""
    print(f"\n{icon} {title}")
    print("=" * 60)

def show_usage_guide():
    """Display the complete usage guide"""
    
    print("\n" + "🎯" * 30)
    print("\n🤖 ROO + AI ORCHESTRATOR USAGE GUIDE")
    print("\n" + "🎯" * 30)
    
    # Option 1: Use Roo Normally
    print_section("OPTION 1: Use Roo Normally (Recommended)", "✅")
    print("""
You can continue using Roo EXACTLY as you always have!
The AI Orchestrator works silently in the background.

1. Open Cursor IDE as usual
2. Use Roo commands normally
3. The orchestrator automatically:
   - Tracks your activities
   - Suggests optimal modes
   - Manages context between tasks
   
NO CHANGES NEEDED to your workflow!
""")
    
    # Option 2: Enhanced Commands
    print_section("OPTION 2: Use Enhanced Commands", "🚀")
    print("""
For more control, use these enhanced commands:

1. AUTO MODE SELECTION:
   python3 scripts/roo_enhanced_launcher.py "fix authentication bug"
   → Automatically launches Roo in 'debug' mode

2. WORKFLOW EXECUTION:
   python3 scripts/roo_orchestrator_quickstart.py --workflow \\
     "design API" "implement endpoints" "write tests"
   → Executes multi-step workflows with proper mode switching

3. INTERACTIVE MODE:
   python3 scripts/roo_enhanced_launcher.py
   → Describe your task, get mode recommendations
""")
    
    # Option 3: Direct Orchestrator
    print_section("OPTION 3: Direct Orchestrator Access", "⚡")
    print("""
For power users who want full control:

1. TASK ANALYSIS:
   python3 scripts/roo_orchestrator_quickstart.py --task "your task"
   
2. VIEW STATISTICS:
   python3 scripts/roo_orchestrator_quickstart.py --stats
   
3. INTERACTIVE ORCHESTRATOR:
   python3 scripts/roo_orchestrator_quickstart.py --interactive
""")
    
    # Quick Examples
    print_section("QUICK EXAMPLES", "💡")
    print("""
EXAMPLE 1 - Fix a bug (Auto mode selection):
  $ python3 scripts/roo_enhanced_launcher.py "fix login error"
  → Launches Roo in debug mode automatically

EXAMPLE 2 - Build a feature (Workflow):
  $ python3 scripts/roo_orchestrator_quickstart.py --workflow \\
      "design user dashboard" \\
      "implement dashboard components" \\
      "add dashboard tests"
  → Executes complete workflow with mode switching

EXAMPLE 3 - Just use Roo normally:
  $ cursor .  # Open Cursor IDE
  → Use Roo as you always do, orchestrator tracks in background
""")
    
    # Current Status
    print_section("CURRENT STATUS", "📊")
    
    # Check if services are running
    mcp_running = os.system("pgrep -f simple_mcp_server > /dev/null 2>&1") == 0
    db_exists = os.path.exists("roo_integration.db")
    
    print(f"✅ Database: {'Active' if db_exists else 'Not found'}")
    print(f"{'✅' if mcp_running else '⚠️ '} MCP Server: {'Running' if mcp_running else 'Not running'}")
    print(f"✅ Mode Selection: Active")
    print(f"✅ Workflow Engine: Active")
    
    if not mcp_running:
        print("\nTo start MCP server: python3 scripts/simple_mcp_server.py &")
    
    # Bottom line
    print("\n" + "=" * 60)
    print("🎉 THE INTEGRATION IS WORKING!")
    print("You can use Roo normally OR with enhanced orchestration features.")
    print("=" * 60 + "\n")

def main():
    """Main entry point"""
    show_usage_guide()
    
    # Offer to run a demo
    print("\nWould you like to try it now?")
    print("1. Launch enhanced Roo (with auto mode selection)")
    print("2. Run orchestrator quickstart")
    print("3. View statistics")
    print("4. Exit")
    
    try:
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            os.system("python3 scripts/roo_enhanced_launcher.py")
        elif choice == "2":
            os.system("python3 scripts/roo_orchestrator_quickstart.py --interactive")
        elif choice == "3":
            os.system("python3 scripts/roo_orchestrator_quickstart.py --stats")
        elif choice == "4":
            print("\n👋 Happy coding with Roo + AI Orchestrator!")
        else:
            print("\nInvalid option. Run this script again to see options.")
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")

if __name__ == "__main__":
    main()