#!/usr/bin/env python3
"""
Git Intelligence MCP Server - Provides Git history and change analysis for AI coding.
"""

import asyncio
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import TextContent, Tool


class GitIntelligenceServer:
    """MCP server for Git intelligence and change analysis."""

    def __init__(self):
        self.server = Server("git-intelligence")
        self.project_root = Path.cwd()
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP handlers for Git intelligence tools."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="git_recent_changes",
                    description="Show recent changes in the repository with commit messages",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {"type": "integer", "description": "Number of days to look back", "default": 7},
                            "file_path": {"type": "string", "description": "Specific file to check (optional)"},
                            "author": {"type": "string", "description": "Filter by author (optional)"}
                        }
                    }
                ),
                Tool(
                    name="git_blame_analysis",
                    description="Show who changed each line of a file and when",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "File to analyze"},
                            "start_line": {"type": "integer", "description": "Start line number (optional)"},
                            "end_line": {"type": "integer", "description": "End line number (optional)"}
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="git_diff_analysis",
                    description="Analyze changes between commits, branches, or working directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "from_ref": {"type": "string", "description": "Source reference (commit/branch)", "default": "HEAD~1"},
                            "to_ref": {"type": "string", "description": "Target reference (commit/branch)", "default": "HEAD"},
                            "file_path": {"type": "string", "description": "Specific file to diff (optional)"},
                            "stat_only": {"type": "boolean", "description": "Show only file statistics", "default": False}
                        }
                    }
                ),
                Tool(
                    name="git_file_history",
                    description="Show complete change history for a specific file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "File to get history for"},
                            "max_commits": {"type": "integer", "description": "Maximum commits to show", "default": 10}
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="git_branch_analysis",
                    description="Analyze branch differences and merge status",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "branch": {"type": "string", "description": "Branch to analyze (default: current)"},
                            "compare_to": {"type": "string", "description": "Base branch to compare", "default": "main"}
                        }
                    }
                ),
                Tool(
                    name="git_hotspot_analysis",
                    description="Find code hotspots - files that change frequently",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {"type": "integer", "description": "Days to analyze", "default": 30},
                            "min_changes": {"type": "integer", "description": "Minimum changes to include", "default": 3}
                        }
                    }
                ),
                Tool(
                    name="git_contributor_stats",
                    description="Show contributor statistics and code ownership",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {"type": "integer", "description": "Days to analyze", "default": 90},
                            "file_path": {"type": "string", "description": "Specific file/directory (optional)"}
                        }
                    }
                ),
                Tool(
                    name="git_related_changes",
                    description="Find files that often change together",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Reference file"},
                            "days": {"type": "integer", "description": "Days to analyze", "default": 60}
                        },
                        "required": ["file_path"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            
            if name == "git_recent_changes":
                return await self._git_recent_changes(arguments)
            elif name == "git_blame_analysis":
                return await self._git_blame_analysis(arguments)
            elif name == "git_diff_analysis":
                return await self._git_diff_analysis(arguments)
            elif name == "git_file_history":
                return await self._git_file_history(arguments)
            elif name == "git_branch_analysis":
                return await self._git_branch_analysis(arguments)
            elif name == "git_hotspot_analysis":
                return await self._git_hotspot_analysis(arguments)
            elif name == "git_contributor_stats":
                return await self._git_contributor_stats(arguments)
            elif name == "git_related_changes":
                return await self._git_related_changes(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def _run_git_command(self, args: List[str]) -> Optional[str]:
        """Run a git command and return output."""
        try:
            result = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    async def _git_recent_changes(self, args: Dict[str, Any]) -> List[TextContent]:
        """Show recent changes in the repository."""
        days = args.get("days", 7)
        file_path = args.get("file_path")
        author = args.get("author")
        
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        git_args = [
            "log", 
            "--oneline", 
            "--since", since_date,
            "--pretty=format:%h|%an|%ad|%s",
            "--date=relative"
        ]
        
        if author:
            git_args.extend(["--author", author])
        
        if file_path:
            git_args.append("--")
            git_args.append(file_path)
        
        output = await self._run_git_command(git_args)
        
        if not output:
            return [TextContent(type="text", text=f"No recent changes found in the last {days} days.")]
        
        result = f"# Recent Changes (Last {days} days)\n\n"
        
        for line in output.split('\n'):
            if '|' in line:
                hash_short, author_name, date, message = line.split('|', 3)
                result += f"**{hash_short}** by {author_name} ({date})\n"
                result += f"  {message}\n\n"
        
        return [TextContent(type="text", text=result)]

    async def _git_blame_analysis(self, args: Dict[str, Any]) -> List[TextContent]:
        """Show blame analysis for a file."""
        file_path = args["file_path"]
        start_line = args.get("start_line")
        end_line = args.get("end_line")
        
        if not Path(file_path).exists():
            return [TextContent(type="text", text=f"File not found: {file_path}")]
        
        git_args = ["blame", "--line-porcelain", file_path]
        
        if start_line and end_line:
            git_args.extend(["-L", f"{start_line},{end_line}"])
        
        output = await self._run_git_command(git_args)
        
        if not output:
            return [TextContent(type="text", text=f"Unable to get blame information for {file_path}")]
        
        result = f"# Blame Analysis: {file_path}\n\n"
        
        # Parse porcelain output
        lines = output.split('\n')
        commits = {}
        line_info = []
        
        i = 0
        while i < len(lines):
            if lines[i].startswith('\t'):
                # This is the actual code line
                code_line = lines[i][1:]  # Remove tab
                line_info.append(code_line)
                i += 1
            else:
                # Parse commit info
                commit_hash = lines[i].split()[0]
                if commit_hash not in commits:
                    commits[commit_hash] = {}
                
                # Look for author and date info
                while i < len(lines) and not lines[i].startswith('\t'):
                    if lines[i].startswith('author '):
                        commits[commit_hash]['author'] = lines[i][7:]
                    elif lines[i].startswith('author-time '):
                        timestamp = int(lines[i][12:])
                        commits[commit_hash]['date'] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                    i += 1
        
        # Show summary
        result += f"**Total lines analyzed**: {len(line_info)}\n"
        result += f"**Commits involved**: {len(commits)}\n\n"
        
        # Show top contributors
        authors = {}
        for commit_info in commits.values():
            author = commit_info.get('author', 'Unknown')
            authors[author] = authors.get(author, 0) + 1
        
        result += "**Top Contributors**:\n"
        for author, count in sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5]:
            result += f"- {author}: {count} lines\n"
        
        return [TextContent(type="text", text=result)]

    async def _git_diff_analysis(self, args: Dict[str, Any]) -> List[TextContent]:
        """Analyze differences between refs."""
        from_ref = args.get("from_ref", "HEAD~1")
        to_ref = args.get("to_ref", "HEAD")
        file_path = args.get("file_path")
        stat_only = args.get("stat_only", False)
        
        if stat_only:
            git_args = ["diff", "--stat", from_ref, to_ref]
        else:
            git_args = ["diff", "--unified=3", from_ref, to_ref]
        
        if file_path:
            git_args.append("--")
            git_args.append(file_path)
        
        output = await self._run_git_command(git_args)
        
        if not output:
            return [TextContent(type="text", text=f"No differences found between {from_ref} and {to_ref}")]
        
        result = f"# Diff Analysis: {from_ref} → {to_ref}\n\n"
        
        if stat_only:
            result += "**File Statistics**:\n```\n"
            result += output
            result += "\n```"
        else:
            # Parse and format diff
            lines = output.split('\n')
            in_diff = False
            
            for line in lines:
                if line.startswith('diff --git'):
                    file_name = line.split()[-1].replace('b/', '')
                    result += f"\n**{file_name}**:\n```diff\n"
                    in_diff = True
                elif line.startswith('+++') or line.startswith('---'):
                    continue
                elif line.startswith('@@'):
                    result += line + '\n'
                elif in_diff:
                    result += line + '\n'
            
            if in_diff:
                result += "```"
        
        return [TextContent(type="text", text=result)]

    async def _git_file_history(self, args: Dict[str, Any]) -> List[TextContent]:
        """Show file history."""
        file_path = args["file_path"]
        max_commits = args.get("max_commits", 10)
        
        if not Path(file_path).exists():
            return [TextContent(type="text", text=f"File not found: {file_path}")]
        
        git_args = [
            "log", 
            f"--max-count={max_commits}",
            "--pretty=format:%h|%an|%ad|%s",
            "--date=short",
            "--follow",
            "--",
            file_path
        ]
        
        output = await self._run_git_command(git_args)
        
        if not output:
            return [TextContent(type="text", text=f"No history found for {file_path}")]
        
        result = f"# File History: {file_path}\n\n"
        
        for line in output.split('\n'):
            if '|' in line:
                hash_short, author, date, message = line.split('|', 3)
                result += f"**{hash_short}** ({date}) by {author}\n"
                result += f"  {message}\n\n"
        
        return [TextContent(type="text", text=result)]

    async def _git_branch_analysis(self, args: Dict[str, Any]) -> List[TextContent]:
        """Analyze branch differences."""
        branch = args.get("branch", "HEAD")
        compare_to = args.get("compare_to", "main")
        
        # Get current branch if not specified
        if branch == "HEAD":
            current_branch = await self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
            branch = current_branch or "HEAD"
        
        # Check commits ahead/behind
        ahead_output = await self._run_git_command(["rev-list", "--count", f"{compare_to}..{branch}"])
        behind_output = await self._run_git_command(["rev-list", "--count", f"{branch}..{compare_to}"])
        
        ahead = int(ahead_output) if ahead_output else 0
        behind = int(behind_output) if behind_output else 0
        
        result = f"# Branch Analysis: {branch}\n\n"
        result += f"**Compared to {compare_to}**:\n"
        result += f"- Commits ahead: {ahead}\n"
        result += f"- Commits behind: {behind}\n\n"
        
        if ahead > 0:
            # Show unique commits
            unique_commits = await self._run_git_command([
                "log", "--oneline", f"{compare_to}..{branch}"
            ])
            if unique_commits:
                result += f"**Unique commits in {branch}**:\n"
                for commit in unique_commits.split('\n')[:10]:  # Limit to 10
                    result += f"- {commit}\n"
        
        return [TextContent(type="text", text=result)]

    async def _git_hotspot_analysis(self, args: Dict[str, Any]) -> List[TextContent]:
        """Find frequently changed files."""
        days = args.get("days", 30)
        min_changes = args.get("min_changes", 3)
        
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        output = await self._run_git_command([
            "log", "--since", since_date, "--name-only", "--pretty=format:"
        ])
        
        if not output:
            return [TextContent(type="text", text=f"No changes found in the last {days} days")]
        
        # Count file changes
        file_changes = {}
        for line in output.split('\n'):
            line = line.strip()
            if line and not line.startswith('.'):
                file_changes[line] = file_changes.get(line, 0) + 1
        
        # Filter and sort
        hotspots = [(f, count) for f, count in file_changes.items() if count >= min_changes]
        hotspots.sort(key=lambda x: x[1], reverse=True)
        
        result = f"# Code Hotspots (Last {days} days)\n\n"
        result += f"Files changed ≥{min_changes} times:\n\n"
        
        for file_path, count in hotspots[:20]:  # Top 20
            result += f"**{file_path}**: {count} changes\n"
        
        return [TextContent(type="text", text=result)]

    async def _git_contributor_stats(self, args: Dict[str, Any]) -> List[TextContent]:
        """Show contributor statistics."""
        days = args.get("days", 90)
        file_path = args.get("file_path")
        
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        git_args = ["shortlog", "-sn", "--since", since_date]
        if file_path:
            git_args.extend(["--", file_path])
        
        output = await self._run_git_command(git_args)
        
        if not output:
            return [TextContent(type="text", text=f"No contributor data found for the last {days} days")]
        
        result = f"# Contributor Stats (Last {days} days)\n\n"
        if file_path:
            result += f"**File/Directory**: {file_path}\n\n"
        
        result += "**Commits by Author**:\n"
        for line in output.split('\n'):
            if line.strip():
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    count, author = parts
                    result += f"- {author}: {count} commits\n"
        
        return [TextContent(type="text", text=result)]

    async def _git_related_changes(self, args: Dict[str, Any]) -> List[TextContent]:
        """Find files that often change together."""
        file_path = args["file_path"]
        days = args.get("days", 60)
        
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Get commits that touched the target file
        commits_output = await self._run_git_command([
            "log", "--since", since_date, "--pretty=format:%H", "--", file_path
        ])
        
        if not commits_output:
            return [TextContent(type="text", text=f"No recent changes found for {file_path}")]
        
        commits = commits_output.split('\n')
        
        # For each commit, get all files changed
        related_files = {}
        for commit_hash in commits[:20]:  # Limit to recent 20 commits
            files_output = await self._run_git_command([
                "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash
            ])
            
            if files_output:
                for f in files_output.split('\n'):
                    f = f.strip()
                    if f and f != file_path:
                        related_files[f] = related_files.get(f, 0) + 1
        
        result = f"# Related Changes: {file_path}\n\n"
        result += f"Files that often change together (last {days} days):\n\n"
        
        # Sort by frequency
        sorted_files = sorted(related_files.items(), key=lambda x: x[1], reverse=True)
        
        for related_file, count in sorted_files[:15]:  # Top 15
            result += f"**{related_file}**: {count} co-changes\n"
        
        return [TextContent(type="text", text=result)]

    async def run(self):
        """Run the MCP server."""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="git-intelligence",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


if __name__ == "__main__":
    server = GitIntelligenceServer()
    asyncio.run(server.run()) 