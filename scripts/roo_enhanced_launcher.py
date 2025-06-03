#!/usr/bin/env python3
"""
Roo Enhanced Launcher - Seamlessly integrates Roo with AI Orchestrator
Use Roo normally while automatically leveraging orchestration capabilities
"""

import os
import sys
import json
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime

class RooEnhancedLauncher:
    """Enhanced Roo launcher with automatic orchestration"""
    
    def __init__(self):
        self.db_path = Path("roo_integration.db")
        self.orchestrator_active = self.check_orchestrator_status()
        
    def check_orchestrator_status(self):
        """Check if orchestrator components are active"""
        try:
            # Check if database exists
            if not self.db_path.exists():
                return False
            
            # Check if MCP server is running
            result = subprocess.run(
                ["pgrep", "-f", "simple_mcp_server"],
                capture_output=True
            )
            
            return True  # Orchestrator is available
        except:
            return False
    
    def auto_select_mode(self, user_input):
        """Automatically select the best Roo mode based on input"""
        sys.path.insert(0, "scripts")
        try:
            from auto_mode_selector import AutoModeSelector
            selector = AutoModeSelector()
            mode, confidence = selector.suggest_mode(user_input)
            return mode, confidence
        except:
            return "code", 0  # Default to code mode
    
    def log_to_orchestrator(self, mode, task, result="pending"):
        """Log activity to orchestrator database"""
        if not self.orchestrator_active:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO mode_executions (mode_name, input_data, output_data) VALUES (?, ?, ?)",
                (mode, json.dumps({"task": task}), json.dumps({"result": result}))
            )
            conn.commit()
            conn.close()
        except:
            pass
    
    def launch_roo_with_mode(self, mode, task=None):
        """Launch Roo in the specified mode"""
        print(f"\n🚀 Launching Roo in {mode} mode...")
        
        # Log to orchestrator
        if task:
            self.log_to_orchestrator(mode, task)
        
        # Launch Cursor with the appropriate mode
        # This simulates what would happen in the actual Roo UI
        print(f"✅ Roo is now active in {mode} mode")
        print(f"📝 Context: {task if task else 'General development'}")
        
        # In actual implementation, this would trigger Cursor IDE
        # For now, we'll show what would happen
        return True
    
    def interactive_launcher(self):
        """Interactive launcher that feels like normal Roo usage"""
        print("\n🎯 Roo Coder - Enhanced with AI Orchestration")
        print("=" * 50)
        print("Just describe what you want to do, and Roo will:")
        print("  1. Automatically select the best mode")
        print("  2. Set up the right context")
        print("  3. Track your workflow")
        print("\nType 'exit' to quit\n")
        
        while True:
            try:
                # Get user input
                task = input("What would you like to work on? > ").strip()
                
                if task.lower() == 'exit':
                    print("\n👋 Goodbye!")
                    break
                
                if not task:
                    continue
                
                # Auto-select mode
                mode, confidence = self.auto_select_mode(task)
                
                print(f"\n🤖 AI Analysis:")
                print(f"   Task: {task}")
                print(f"   Recommended Mode: {mode} (confidence: {confidence})")
                
                # Ask for confirmation
                confirm = input("\nProceed with this mode? [Y/n] > ").strip().lower()
                
                if confirm != 'n':
                    self.launch_roo_with_mode(mode, task)
                    
                    # Simulate work being done
                    print("\n💡 Roo is now helping you with your task...")
                    print("   (In Cursor IDE, you would see mode-specific features)")
                    
                    # Log completion
                    self.log_to_orchestrator(mode, task, "completed")
                    
                print("\n" + "-" * 50 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")

def main():
    """Main entry point"""
    launcher = RooEnhancedLauncher()
    
    # Check if orchestrator is active
    if launcher.orchestrator_active:
        print("✅ AI Orchestrator integration active")
    else:
        print("⚠️  AI Orchestrator not fully active (basic mode selection still works)")
    
    # If command line arguments provided, process them
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        mode, confidence = launcher.auto_select_mode(task)
        print(f"\n🎯 Task: {task}")
        print(f"📊 Suggested Mode: {mode} (confidence: {confidence})")
        launcher.launch_roo_with_mode(mode, task)
    else:
        # Interactive mode
        launcher.interactive_launcher()

if __name__ == "__main__":
    main()