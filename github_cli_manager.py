#!/usr/bin/env python3
"""
🚀 GitHub CLI Automation Suite for Orchestra AI
Comprehensive repository management and automation tools
"""

import subprocess
import json
import sys
from datetime import datetime, timedelta

class GitHubCLIManager:
    def __init__(self, repo="ai-cherry/orchestra-main"):
        self.repo = repo
        
    def run_gh_command(self, command):
        """Execute GitHub CLI command and return result"""
        try:
            result = subprocess.run(
                f"gh {command}",
                shell=True,
                capture_output=True,
                text=True,
                cwd="/home/ubuntu/orchestra-main"
            )
            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def authenticate_status(self):
        """Check GitHub CLI authentication status"""
        return self.run_gh_command("auth status")
    
    def list_pull_requests(self, state="open", label=None):
        """List pull requests with optional filtering"""
        cmd = f"pr list --repo {self.repo} --state {state} --json number,title,author,labels,createdAt,headRefName"
        if label:
            cmd += f" --label {label}"
        return self.run_gh_command(cmd)
    
    def close_pull_request(self, pr_number, comment=None):
        """Close a pull request with optional comment"""
        cmd = f"pr close {pr_number} --repo {self.repo}"
        if comment:
            cmd += f' --comment "{comment}"'
        return self.run_gh_command(cmd)
    
    def delete_branch(self, branch_name, force=False):
        """Delete a branch (remote)"""
        cmd = f"api repos/{self.repo}/git/refs/heads/{branch_name} --method DELETE"
        return self.run_gh_command(cmd)
    
    def list_branches(self):
        """List all branches"""
        return self.run_gh_command(f"api repos/{self.repo}/branches --paginate")
    
    def get_repository_info(self):
        """Get comprehensive repository information"""
        return self.run_gh_command(f"repo view {self.repo} --json name,description,defaultBranch,visibility,pushedAt,updatedAt")
    
    def cleanup_dependabot_prs(self, dry_run=True):
        """Clean up outdated dependabot pull requests"""
        print("🔍 Analyzing dependabot pull requests...")
        
        # Get all open PRs
        prs_result = self.list_pull_requests()
        if not prs_result["success"]:
            return {"success": False, "error": f"Failed to list PRs: {prs_result['error']}"}
        
        try:
            prs = json.loads(prs_result["output"])
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse PR list"}
        
        # Filter dependabot PRs (check both possible formats)
        dependabot_prs = [
            pr for pr in prs 
            if pr["author"]["login"] in ["dependabot[bot]", "app/dependabot"]
        ]
        
        print(f"📊 Found {len(dependabot_prs)} dependabot PRs")
        
        cleanup_results = []
        for pr in dependabot_prs:
            pr_info = {
                "number": pr["number"],
                "title": pr["title"],
                "branch": pr["headRefName"],
                "created": pr["createdAt"]
            }
            
            if dry_run:
                print(f"🔍 Would close PR #{pr['number']}: {pr['title']}")
                cleanup_results.append({"pr": pr_info, "action": "would_close", "success": True})
            else:
                # Close the PR
                close_result = self.close_pull_request(
                    pr["number"], 
                    "Closing outdated dependency update - superseded by comprehensive updates"
                )
                
                if close_result["success"]:
                    print(f"✅ Closed PR #{pr['number']}: {pr['title']}")
                    
                    # Delete the branch
                    delete_result = self.delete_branch(pr["headRefName"])
                    if delete_result["success"]:
                        print(f"🗑️ Deleted branch: {pr['headRefName']}")
                    else:
                        print(f"⚠️ Failed to delete branch {pr['headRefName']}: {delete_result.get('error', 'Unknown error')}")
                    
                    cleanup_results.append({
                        "pr": pr_info, 
                        "action": "closed", 
                        "success": True,
                        "branch_deleted": delete_result["success"]
                    })
                else:
                    print(f"❌ Failed to close PR #{pr['number']}: {close_result.get('error', 'Unknown error')}")
                    cleanup_results.append({
                        "pr": pr_info, 
                        "action": "failed", 
                        "success": False,
                        "error": close_result.get('error', 'Unknown error')
                    })
        
        return {
            "success": True,
            "total_prs": len(dependabot_prs),
            "results": cleanup_results,
            "dry_run": dry_run
        }
    
    def generate_automation_scripts(self):
        """Generate useful automation scripts for future use"""
        scripts = {
            "cleanup_dependabot.sh": """#!/bin/bash
# Quick dependabot cleanup script
echo "🧹 Cleaning up dependabot PRs..."
python3 github_cli_manager.py cleanup --execute
""",
            "repo_status.sh": """#!/bin/bash
# Repository status check
echo "📊 Repository Status Report"
echo "=========================="
gh pr list --repo ai-cherry/orchestra-main
echo ""
echo "Recent commits:"
gh api repos/ai-cherry/orchestra-main/commits --jq '.[0:5] | .[] | "\\(.commit.author.date) - \\(.commit.message | split("\\n")[0])"'
""",
            "branch_cleanup.sh": """#!/bin/bash
# Clean up merged branches
echo "🌿 Cleaning up merged branches..."
gh api repos/ai-cherry/orchestra-main/branches --jq '.[] | select(.name != "main") | .name' | while read branch; do
    echo "Checking branch: $branch"
    # Add logic to check if branch is merged and safe to delete
done
"""
        }
        
        for filename, content in scripts.items():
            with open(f"/home/ubuntu/orchestra-main/scripts/{filename}", "w") as f:
                f.write(content)
            subprocess.run(f"chmod +x /home/ubuntu/orchestra-main/scripts/{filename}", shell=True)
        
        print("✅ Generated automation scripts in /home/ubuntu/orchestra-main/scripts/")
        return scripts

def main():
    """Main CLI interface"""
    manager = GitHubCLIManager()
    
    if len(sys.argv) < 2:
        print("🚀 GitHub CLI Manager for Orchestra AI")
        print("Usage:")
        print("  python3 github_cli_manager.py status")
        print("  python3 github_cli_manager.py cleanup [--execute]")
        print("  python3 github_cli_manager.py generate-scripts")
        return
    
    command = sys.argv[1]
    
    if command == "status":
        # Check authentication and repo status
        auth_status = manager.authenticate_status()
        print("🔐 Authentication Status:")
        print(auth_status["output"] if auth_status["success"] else auth_status["error"])
        
        repo_info = manager.get_repository_info()
        if repo_info["success"]:
            info = json.loads(repo_info["output"])
            print(f"\n📊 Repository: {info['name']}")
            print(f"🔒 Visibility: {info['visibility']}")
            print(f"🌿 Default Branch: {info['defaultBranch']}")
            print(f"📅 Last Updated: {info['updatedAt']}")
    
    elif command == "cleanup":
        dry_run = "--execute" not in sys.argv
        result = manager.cleanup_dependabot_prs(dry_run=dry_run)
        
        if result["success"]:
            print(f"\n📊 Cleanup Summary:")
            print(f"Total dependabot PRs: {result['total_prs']}")
            print(f"Dry run: {result['dry_run']}")
            
            if not dry_run:
                successful = sum(1 for r in result['results'] if r['success'])
                print(f"Successfully processed: {successful}/{result['total_prs']}")
        else:
            print(f"❌ Cleanup failed: {result['error']}")
    
    elif command == "generate-scripts":
        manager.generate_automation_scripts()
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()

