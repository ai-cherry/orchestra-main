#!/usr/bin/env python3
"""
mcp_template_manager.py - Helper utility for managing MCP templates and integrations

This script provides utilities for working with Model Context Protocol (MCP) templates 
across different AI tools and workflows. It supports listing, creating, and applying 
templates for memory system operations.
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("mcp-manager")

# Import MCP templates from roo_workflow_manager if available
try:
    from roo_workflow_manager import MCP_WORKFLOW_TEMPLATES, MemoryBank
    ROO_AVAILABLE = True
except ImportError:
    logger.warning("Roo workflow manager not available. Some features will be limited.")
    ROO_AVAILABLE = False
    # Define fallback templates
    MCP_WORKFLOW_TEMPLATES = {}
    
    # Define fallback MemoryBank
    class MemoryBank:
        """Fallback MemoryBank when Roo is not available."""
        
        @staticmethod
        def save(key: str, content: str) -> bool:
            """Save content to memory."""
            logger.info(f"Fallback save to memory: {key}")
            try:
                os.makedirs("./mcp_memory", exist_ok=True)
                with open(f"./mcp_memory/{key}.json", "w") as f:
                    f.write(content)
                return True
            except Exception as e:
                logger.error(f"Failed to save to memory: {e}")
                return False

        @staticmethod
        def retrieve(key: str) -> Optional[str]:
            """Retrieve content from memory."""
            logger.info(f"Fallback retrieve from memory: {key}")
            try:
                with open(f"./mcp_memory/{key}.json", "r") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to retrieve from memory: {e}")
                return None
        
        @staticmethod
        def update(key: str, content: str) -> bool:
            """Update content in memory."""
            return MemoryBank.save(key, content)

# Extended MCP templates with more detailed descriptions
EXTENDED_MCP_TEMPLATES = {
    "memory_system_review": {
        "description": "Analyze and evaluate the current memory system architecture and implementation",
        "use_cases": ["Identifying bottlenecks", "Evaluating MCP compatibility", "Security assessment"],
        "tools": ["co-pilot", "gemini", "agno"],
        "subtasks": MCP_WORKFLOW_TEMPLATES.get("memory_system_review", [])
    },
    "mcp_integration": {
        "description": "Design and implement MCP support for an existing system",
        "use_cases": ["Adding cross-agent memory", "Implementing persistence", "Enhancing context sharing"],
        "tools": ["co-pilot", "gemini", "agno"],
        "subtasks": MCP_WORKFLOW_TEMPLATES.get("mcp_integration", [])
    },
    "mcp_performance_optimization": {
        "description": "Identify and resolve MCP performance bottlenecks",
        "use_cases": ["Memory usage reduction", "Query optimization", "Caching strategy"],
        "tools": ["co-pilot", "gemini", "agno"],
        "subtasks": MCP_WORKFLOW_TEMPLATES.get("mcp_performance_optimization", [])
    },
    "mcp_security_assessment": {
        "description": "Assess the security of MCP implementations and suggest improvements",
        "use_cases": ["Access control review", "Data classification", "Encryption assessment"],
        "tools": ["co-pilot", "gemini"],
        "subtasks": [
            {
                "type": "mode",
                "mode": "architect",
                "task": "Analyze the current MCP security architecture. Focus on authentication, authorization, and data protection."
            },
            {
                "type": "mode",
                "mode": "reviewer",
                "task": "Review the MCP security implementation for vulnerabilities and compliance with best practices."
            },
            {
                "type": "mode",
                "mode": "strategy",
                "task": "Develop a strategy for enhancing MCP security. Consider encryption, access controls, and secure integration patterns."
            }
        ]
    },
    "cross_tool_mcp_integration": {
        "description": "Implement consistent MCP experience across different AI tools",
        "use_cases": ["Co-pilot integration", "Gemini integration", "Agno integration"],
        "tools": ["co-pilot", "gemini", "agno"],
        "subtasks": [
            {
                "type": "mode",
                "mode": "architect",
                "task": "Design a consistent MCP interface that can be used across different AI tools (Co-pilot, Gemini, Agno)."
            },
            {
                "type": "mode",
                "mode": "code",
                "task": "Implement adapters for each tool to use the common MCP interface."
            },
            {
                "type": "mode",
                "mode": "reviewer",
                "task": "Review the implementation to ensure consistency, security, and performance across all tools."
            }
        ]
    }
}

# Update the existing templates with extended information
for key, template in MCP_WORKFLOW_TEMPLATES.items():
    if key not in EXTENDED_MCP_TEMPLATES:
        EXTENDED_MCP_TEMPLATES[key] = {
            "description": f"MCP workflow for {key}",
            "use_cases": ["General purpose"],
            "tools": ["roo"],
            "subtasks": template
        }

# Natural language patterns that map to specific templates
NL_TEMPLATE_PATTERNS = [
    {
        "patterns": ["review memory system", "analyze memory", "evaluate mcp implementation", 
                     "check memory architecture", "assess current memory system"],
        "template": "memory_system_review"
    },
    {
        "patterns": ["add mcp support", "integrate mcp", "implement memory protocol", 
                     "add cross-agent memory", "enable mcp"],
        "template": "mcp_integration"
    },
    {
        "patterns": ["optimize memory performance", "speed up mcp", "improve memory efficiency", 
                     "reduce token usage", "memory performance issues"],
        "template": "mcp_performance_optimization"
    },
    {
        "patterns": ["security of memory system", "secure mcp", "protect memory data", 
                     "memory system vulnerabilities", "mcp security"],
        "template": "mcp_security_assessment"
    },
    {
        "patterns": ["consistent mcp across tools", "integrate co-pilot and gemini", 
                     "unify memory across tools", "shared memory system"],
        "template": "cross_tool_mcp_integration"
    }
]

class MCPTemplateManager:
    """Manages MCP templates and their application across different tools."""
    
    def __init__(self):
        self.memory = MemoryBank()
        self.templates = EXTENDED_MCP_TEMPLATES
    
    def list_templates(self, format: str = "text") -> Union[str, Dict]:
        """List all available MCP templates."""
        if format == "json":
            return self.templates
        
        output = "Available MCP Templates:\n"
        for name, info in self.templates.items():
            output += f"\n== {name} ==\n"
            output += f"Description: {info['description']}\n"
            output += f"Use cases: {', '.join(info['use_cases'])}\n"
            output += f"Compatible tools: {', '.join(info['tools'])}\n"
            output += f"Number of subtasks: {len(info['subtasks'])}\n"
            
            # Show subtasks if requested
            if format == "verbose":
                output += "Subtasks:\n"
                for i, subtask in enumerate(info['subtasks']):
                    if subtask['type'] == 'mode':
                        task_desc = subtask['task'][:60] + "..." if len(subtask['task']) > 60 else subtask['task']
                        output += f"  {i+1}. [{subtask['mode']}] {task_desc}\n"
                    else:
                        output += f"  {i+1}. [{subtask['type']}] operation: {subtask.get('operation', 'N/A')}\n"
        
        return output
    
    def get_template(self, name: str) -> Optional[Dict]:
        """Get a specific template by name."""
        return self.templates.get(name)
    
    def detect_template_from_text(self, text: str) -> Optional[str]:
        """Detect the most appropriate template based on natural language text."""
        text = text.lower()
        
        # Check for exact matches in patterns
        for pattern_info in NL_TEMPLATE_PATTERNS:
            for pattern in pattern_info["patterns"]:
                if pattern in text:
                    logger.info(f"Detected template '{pattern_info['template']}' from pattern '{pattern}'")
                    return pattern_info["template"]
        
        # Check for keyword matches
        keyword_scores = {name: 0 for name in self.templates.keys()}
        for name, info in self.templates.items():
            # Check description
            if any(word in text for word in info["description"].lower().split()):
                keyword_scores[name] += 2
            
            # Check use cases
            for use_case in info["use_cases"]:
                if any(word in text for word in use_case.lower().split()):
                    keyword_scores[name] += 1
        
        # Get the template with the highest score
        best_template = max(keyword_scores.items(), key=lambda x: x[1])
        if best_template[1] > 0:
            logger.info(f"Detected template '{best_template[0]}' from keyword analysis with score {best_template[1]}")
            return best_template[0]
        
        return None
    
    def save_template(self, name: str, template: Dict) -> bool:
        """Save a new or updated template."""
        self.templates[name] = template
        return self.memory.save(f"mcp_template_{name}", json.dumps(template))
    
    def export_for_tool(self, tool: str, template_name: Optional[str] = None) -> Dict:
        """Export templates in a format compatible with the specified tool."""
        if template_name:
            template = self.get_template(template_name)
            if not template:
                raise ValueError(f"Template '{template_name}' not found")
                
            if tool not in template["tools"]:
                logger.warning(f"Template '{template_name}' is not marked as compatible with {tool}")
            
            return self._format_for_tool(tool, template_name, template)
        
        # Export all compatible templates
        result = {}
        for name, template in self.templates.items():
            if tool in template["tools"]:
                result[name] = self._format_for_tool(tool, name, template)
        
        return result
    
    def _format_for_tool(self, tool: str, name: str, template: Dict) -> Dict:
        """Format a template for the specified tool."""
        if tool == "co-pilot":
            return {
                "id": name,
                "name": name.replace("_", " ").title(),
                "description": template["description"],
                "category": "mcp",
                "tasks": [self._convert_subtask_for_copilot(subtask) for subtask in template["subtasks"]],
                "meta": {
                    "use_cases": template["use_cases"],
                    "source": "mcp_template_manager"
                }
            }
        elif tool == "gemini":
            return {
                "template_id": name,
                "display_name": name.replace("_", " ").title(),
                "description": template["description"],
                "use_cases": template["use_cases"],
                "workflow": [self._convert_subtask_for_gemini(subtask) for subtask in template["subtasks"]],
                "metadata": {
                    "source": "mcp_template_manager",
                    "version": "1.0"
                }
            }
        elif tool == "agno":
            return {
                "name": name,
                "description": template["description"],
                "type": "mcp_workflow",
                "steps": [self._convert_subtask_for_agno(subtask) for subtask in template["subtasks"]],
                "metadata": {
                    "use_cases": template["use_cases"],
                    "source": "mcp_template_manager"
                }
            }
        else:
            # Default format
            return {
                "name": name,
                "description": template["description"],
                "use_cases": template["use_cases"],
                "subtasks": template["subtasks"]
            }
    
    def _convert_subtask_for_copilot(self, subtask: Dict) -> Dict:
        """Convert a subtask to Co-pilot format."""
        if subtask["type"] == "mode":
            return {
                "type": "prompt",
                "role": subtask["mode"],
                "content": subtask["task"]
            }
        else:
            return {
                "type": "action",
                "action_type": subtask["type"],
                "parameters": subtask
            }
    
    def _convert_subtask_for_gemini(self, subtask: Dict) -> Dict:
        """Convert a subtask to Gemini format."""
        if subtask["type"] == "mode":
            return {
                "step_type": "prompt",
                "mode": subtask["mode"],
                "prompt": subtask["task"]
            }
        else:
            return {
                "step_type": "operation",
                "operation": subtask["type"],
                "parameters": subtask
            }
    
    def _convert_subtask_for_agno(self, subtask: Dict) -> Dict:
        """Convert a subtask to Agno/Phidata format."""
        if subtask["type"] == "mode":
            return {
                "type": "agent_task",
                "agent": subtask["mode"],
                "task": subtask["task"]
            }
        else:
            return {
                "type": "operation",
                "name": subtask["type"],
                "params": subtask
            }
    
    def generate_config_from_description(self, description: str) -> Dict:
        """Generate an MCP configuration from a natural language description."""
        if not ROO_AVAILABLE:
            logger.warning("Roo not available, using simplified config generation")
            # Basic config generator without Roo
            config = {
                "storage_approach": "default",
                "persistence_level": "session",
                "security_requirements": "standard",
                "token_budget": 1000,
                "integration_points": ["generic"]
            }
            
            # Very basic text analysis
            if "cross-session" in description.lower() or "persist" in description.lower():
                config["persistence_level"] = "cross_session"
            
            if "high security" in description.lower() or "secure" in description.lower():
                config["security_requirements"] = "high"
            
            if "gemini" in description.lower():
                config["integration_points"].append("gemini")
            
            if "co-pilot" in description.lower():
                config["integration_points"].append("co-pilot")
            
            if "agno" in description.lower() or "phidata" in description.lower():
                config["integration_points"].append("agno")
                
            return config
        
        # Use Roo for more sophisticated config generation
        from roo_workflow_manager import RooModeManager
        
        config_prompt = f"""
        Generate an MCP (Model Context Protocol) configuration based on this description:
        
        {description}
        
        Your configuration should include:
        1. storage_approach - How data is stored (e.g., tiered_memory, simple, distributed)
        2. persistence_level - Level of persistence (e.g., session, cross_session, temporary)
        3. security_requirements - Security level (e.g., low, standard, high)
        4. token_budget - Maximum tokens to use (default 1000)
        5. integration_points - List of tools that need MCP access (co-pilot, gemini, agno)
        
        Return only a JSON object with these fields.
        """
        
        try:
            config_json = RooModeManager.execute_in_mode("architect", config_prompt)
            return json.loads(config_json)
        except Exception as e:
            logger.error(f"Error generating config: {e}")
            return self.generate_config_from_description(description)
    
    def detect_mcp_usefulness(self, task_description: str) -> Dict[str, Any]:
        """Analyze a task to determine if MCP would be beneficial and which template would be best."""
        mcp_indicators = [
            "memory management", "persist", "remember", "recall",
            "cross-agent", "communication", "share context", "mcp",
            "context protocol", "shared memory", "memory bank"
        ]
        
        # Check for indicators
        usefulness_score = 0
        matched_indicators = []
        for indicator in mcp_indicators:
            if indicator in task_description.lower():
                usefulness_score += 1
                matched_indicators.append(indicator)
        
        # Detect template
        template_name = self.detect_template_from_text(task_description)
        
        return {
            "useful": usefulness_score > 0,
            "score": usefulness_score,
            "matched_indicators": matched_indicators,
            "recommended_template": template_name
        }

def main():
    """Command line interface for the MCP template manager."""
    parser = argparse.ArgumentParser(description="MCP Template Manager")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List templates command
    list_parser = subparsers.add_parser("list", help="List available MCP templates")
    list_parser.add_argument("--format", choices=["text", "verbose", "json"], default="text",
                           help="Output format (text, verbose, json)")
    
    # Export templates command
    export_parser = subparsers.add_parser("export", help="Export templates for a specific tool")
    export_parser.add_argument("--tool", required=True, choices=["co-pilot", "gemini", "agno"],
                             help="Tool to export for")
    export_parser.add_argument("--template", help="Specific template to export")
    export_parser.add_argument("--output", help="Output file (default: stdout)")
    
    # Detect template command
    detect_parser = subparsers.add_parser("detect", help="Detect appropriate template from text")
    detect_parser.add_argument("--text", required=True, help="Text to analyze")
    
    # Generate config command
    config_parser = subparsers.add_parser("config", help="Generate MCP config from description")
    config_parser.add_argument("--description", required=True, help="Natural language description")
    config_parser.add_argument("--output", help="Output file (default: stdout)")
    
    # Analyze usefulness command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze if MCP would be useful for a task")
    analyze_parser.add_argument("--task", required=True, help="Task description to analyze")
    
    args = parser.parse_args()
    
    template_manager = MCPTemplateManager()
    
    if args.command == "list":
        result = template_manager.list_templates(args.format)
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(result)
    
    elif args.command == "export":
        result = template_manager.export_for_tool(args.tool, args.template)
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"Exported templates to {args.output}")
        else:
            print(json.dumps(result, indent=2))
    
    elif args.command == "detect":
        template_name = template_manager.detect_template_from_text(args.text)
        if template_name:
            template = template_manager.get_template(template_name)
            print(f"Detected template: {template_name}")
            print(f"Description: {template['description']}")
            print(f"Use cases: {', '.join(template['use_cases'])}")
        else:
            print("No matching template found")
    
    elif args.command == "config":
        config = template_manager.generate_config_from_description(args.description)
        if args.output:
            with open(args.output, "w") as f:
                json.dump(config, f, indent=2)
            print(f"Generated config saved to {args.output}")
        else:
            print(json.dumps(config, indent=2))
    
    elif args.command == "analyze":
        result = template_manager.detect_mcp_usefulness(args.task)
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()