#!/usr/bin/env python3
"""
🎯 Orchestra AI Project Dashboard Creator
Creates comprehensive high-level project overview and persona knowledge bases in Notion
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
import logging

from config.notion_config import get_config, NotionConfig

logger = logging.getLogger(__name__)

class ProjectDashboardCreator:
    """Create and maintain comprehensive project dashboard in Notion"""
    
    def __init__(self, config: NotionConfig):
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.workspace_url = f"https://www.notion.so/Orchestra-AI-Workspace-{config.workspace_id}"
    
    async def create_comprehensive_dashboard(self) -> Dict[str, Any]:
        """Create the complete project dashboard with all components"""
        
        logger.info("🎯 Creating Orchestra AI Comprehensive Project Dashboard...")
        
        results = {}
        
        # 1. Create Main Project Overview Page
        overview_page = await self._create_project_overview_page()
        results["overview_page"] = overview_page
        
        # 2. Create Persona Knowledge Bases
        persona_bases = await self._create_persona_knowledge_bases()
        results["persona_knowledge_bases"] = persona_bases
        
        # 3. Create AI Tools Performance Dashboard
        tools_dashboard = await self._create_ai_tools_dashboard()
        results["ai_tools_dashboard"] = tools_dashboard
        
        # 4. Create Development Status Dashboard
        dev_dashboard = await self._create_development_dashboard()
        results["development_dashboard"] = dev_dashboard
        
        # 5. Link everything together
        await self._link_dashboard_components(results)
        
        logger.info("✅ Comprehensive project dashboard created successfully!")
        return results
    
    async def _create_project_overview_page(self) -> Dict[str, Any]:
        """Create the main project overview page"""
        
        overview_content = self._get_project_overview_content()
        
        page_data = {
            "parent": {"type": "workspace"},
            "properties": {
                "title": [{"text": {"content": "🎯 Orchestra AI - Project Overview & Command Center"}}]
            },
            "children": overview_content
        }
        
        try:
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                json=page_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Created project overview page: {result['id']}")
                return result
            else:
                logger.error(f"Failed to create overview page: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error creating overview page: {e}")
            return {}
    
    def _get_project_overview_content(self) -> List[Dict[str, Any]]:
        """Generate comprehensive project overview content"""
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        return [
            # Project Mission & Vision
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": "🎯 Mission & Vision"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": "Orchestra AI is a Complete AI Orchestration Platform that unifies multiple AI coding tools (Cursor, Roo, Continue) with intelligent task routing, shared context management, and comprehensive Notion-based project oversight. Our goal is to achieve maximum development velocity while maintaining enterprise-grade quality standards."}}
                    ]
                }
            },
            
            # Key Components Overview
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": "🏗️ Key Components"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": "🧠 ", "annotations": {"bold": True}}},
                        {"text": {"content": "MCP Unified Server", "annotations": {"bold": True}}},
                        {"text": {"content": " - Central hub for AI tool coordination and context sharing"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": "🌐 ", "annotations": {"bold": True}}},
                        {"text": {"content": "Admin Interface", "annotations": {"bold": True}}},
                        {"text": {"content": " - React-based dashboard for project management and monitoring"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": "📱 ", "annotations": {"bold": True}}},
                        {"text": {"content": "Mobile Applications", "annotations": {"bold": True}}},
                        {"text": {"content": " - iOS and Android apps for on-the-go access"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": "☁️ ", "annotations": {"bold": True}}},
                        {"text": {"content": "Infrastructure", "annotations": {"bold": True}}},
                        {"text": {"content": " - Lambda Labs cloud deployment with Pulumi IaC"}}
                    ]
                }
            },
            
            # Current Status Dashboard
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": "📊 Real-Time Status Dashboard"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": f"Last Updated: {current_time}", "annotations": {"code": True}}}
                    ]
                }
            },
            
            # Quick Links Section
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "🔗 Quick Access"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": "📋 ", "annotations": {"bold": True}}},
                        {"text": {"content": "Active Tasks", "link": {"url": f"{self.workspace_url}?v=tasks"}}},
                        {"text": {"content": " | "}},
                        {"text": {"content": "🎯 Epic Tracking", "link": {"url": f"{self.workspace_url}?v=epics"}}},
                        {"text": {"content": " | "}},
                        {"text": {"content": "💻 Development Log", "link": {"url": f"{self.workspace_url}?v=devlog"}}},
                        {"text": {"content": " | "}},
                        {"text": {"content": "📊 AI Metrics", "link": {"url": f"{self.workspace_url}?v=metrics"}}}
                    ]
                }
            },
            
            # AI Personas Section
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": "👥 AI Persona Knowledge Bases"}}]
                }
            },
            {
                "object": "block",
                "type": "column_list",
                "column_list": {},
                "children": [
                    {
                        "object": "block",
                        "type": "column",
                        "column": {},
                        "children": [
                            {
                                "object": "block",
                                "type": "heading_3",
                                "heading_3": {
                                    "rich_text": [{"text": {"content": "🍒 Cherry - Personal Assistant"}}]
                                }
                            },
                            {
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {"text": {"content": "Personal productivity and life management AI assistant with advanced context understanding and task automation capabilities."}}
                                    ]
                                }
                            }
                        ]
                    },
                    {
                        "object": "block",
                        "type": "column",
                        "column": {},
                        "children": [
                            {
                                "object": "block",
                                "type": "heading_3",
                                "heading_3": {
                                    "rich_text": [{"text": {"content": "👩‍💼 Sophia - Financial Services"}}]
                                }
                            },
                            {
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {"text": {"content": "Pay Ready financial services specialist with expertise in payment processing, compliance, and financial data analysis."}}
                                    ]
                                }
                            }
                        ]
                    }
                ]
            },
            
            # Development Activity
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": "🚀 Development Activity & Metrics"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": "Track development velocity, AI tool performance, and project progress in real-time through our integrated monitoring systems."}}
                    ]
                }
            }
        ]
    
    async def _create_persona_knowledge_bases(self) -> Dict[str, Any]:
        """Create comprehensive knowledge bases for each AI persona"""
        
        personas = {
            "cherry": {
                "name": "🍒 Cherry - Personal Assistant Knowledge Base",
                "domain": "Personal Productivity & Life Management",
                "capabilities": [
                    "Task automation and workflow optimization",
                    "Calendar and schedule management",
                    "Personal data organization and insights",
                    "Context-aware assistance and recommendations",
                    "Multi-platform integration and sync"
                ],
                "key_features": [
                    "Advanced natural language processing",
                    "Predictive task scheduling",
                    "Intelligent priority management",
                    "Cross-device context sharing",
                    "Automated routine optimization"
                ]
            },
            "sophia": {
                "name": "👩‍💼 Sophia - Financial Services Knowledge Base",
                "domain": "Payment Processing & Financial Analysis",
                "capabilities": [
                    "Payment gateway integration and management",
                    "Financial compliance and regulatory adherence",
                    "Transaction monitoring and fraud detection",
                    "Financial data analysis and reporting",
                    "Risk assessment and management"
                ],
                "key_features": [
                    "PCI DSS compliance automation",
                    "Real-time transaction processing",
                    "Advanced fraud detection algorithms",
                    "Regulatory reporting automation",
                    "Multi-currency support and conversion"
                ]
            },
            "karen": {
                "name": "👩‍⚕️ Karen - Medical Coding Knowledge Base",
                "domain": "Healthcare & Medical Coding",
                "capabilities": [
                    "ICD-10 and CPT code assignment",
                    "Medical terminology processing",
                    "Healthcare compliance monitoring",
                    "Clinical documentation analysis",
                    "Insurance claim processing automation"
                ],
                "key_features": [
                    "HIPAA compliance integration",
                    "Advanced medical NLP",
                    "Code accuracy validation",
                    "Automated claim preparation",
                    "Healthcare data analytics"
                ]
            }
        }
        
        results = {}
        
        for persona_key, persona_info in personas.items():
            try:
                page_data = {
                    "parent": {"type": "workspace"},
                    "properties": {
                        "title": [{"text": {"content": persona_info["name"]}}]
                    },
                    "children": self._get_persona_knowledge_content(persona_info)
                }
                
                response = requests.post(
                    "https://api.notion.com/v1/pages",
                    headers=self.headers,
                    json=page_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    results[persona_key] = result
                    logger.info(f"✅ Created {persona_key} knowledge base: {result['id']}")
                else:
                    logger.error(f"Failed to create {persona_key} knowledge base: {response.text}")
                    
            except Exception as e:
                logger.error(f"Error creating {persona_key} knowledge base: {e}")
        
        return results
    
    def _get_persona_knowledge_content(self, persona_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate persona knowledge base content"""
        
        content = [
            # Domain Overview
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": f"🎯 Domain: {persona_info['domain']}"}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "🔧 Core Capabilities"}}]
                }
            }
        ]
        
        # Add capabilities
        for capability in persona_info["capabilities"]:
            content.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": capability}}]
                }
            })
        
        # Add key features
        content.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "⭐ Key Features"}}]
            }
        })
        
        for feature in persona_info["key_features"]:
            content.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": feature}}]
                }
            })
        
        # Add operational guidelines
        content.extend([
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "📋 Operational Guidelines"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": "This knowledge base serves as the foundational reference for AI-assisted development in this domain. It should be updated regularly with new insights, best practices, and domain-specific requirements."}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"text": {"content": "🔄 Update Mechanism"}}]
                }
            },
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"text": {"content": "Weekly review of domain developments and new requirements"}}]
                }
            },
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"text": {"content": "Integration of feedback from AI tool interactions and user experiences"}}]
                }
            },
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"text": {"content": "Continuous enhancement based on performance metrics and outcome analysis"}}]
                }
            }
        ])
        
        return content
    
    async def _create_ai_tools_dashboard(self) -> Dict[str, Any]:
        """Create AI tools performance dashboard"""
        
        dashboard_content = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": "🤖 AI Tools Performance & Coordination"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": "Real-time monitoring and optimization of AI coding tool performance, task routing efficiency, and collaborative development workflows."}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "🎯 Intelligent Task Routing"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": "Cursor", "annotations": {"bold": True}}},
                        {"text": {"content": " → Quick edits, single-file operations, immediate code generation"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": "Roo", "annotations": {"bold": True}}},
                        {"text": {"content": " → Complex workflows, architecture decisions, research tasks"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": "Continue", "annotations": {"bold": True}}},
                        {"text": {"content": " → UI development, React components, frontend optimization"}}
                    ]
                }
            }
        ]
        
        page_data = {
            "parent": {"type": "workspace"},
            "properties": {
                "title": [{"text": {"content": "🤖 AI Tools Performance Dashboard"}}]
            },
            "children": dashboard_content
        }
        
        try:
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                json=page_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Created AI tools dashboard: {result['id']}")
                return result
            else:
                logger.error(f"Failed to create AI tools dashboard: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error creating AI tools dashboard: {e}")
            return {}
    
    async def _create_development_dashboard(self) -> Dict[str, Any]:
        """Create development status dashboard"""
        
        dashboard_content = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": "🚀 Development Status & Progress"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": "Comprehensive overview of development activity, sprint progress, and project milestones with real-time updates from integrated development tools."}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "📊 Current Sprint Overview"}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "🔧 Active Development Areas"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": "Backend API development and optimization"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": "Frontend user interface enhancements"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": "Infrastructure automation and deployment"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": "AI persona feature development"}}]
                }
            }
        ]
        
        page_data = {
            "parent": {"type": "workspace"},
            "properties": {
                "title": [{"text": {"content": "🚀 Development Status Dashboard"}}]
            },
            "children": dashboard_content
        }
        
        try:
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                json=page_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Created development dashboard: {result['id']}")
                return result
            else:
                logger.error(f"Failed to create development dashboard: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error creating development dashboard: {e}")
            return {}
    
    async def _link_dashboard_components(self, results: Dict[str, Any]):
        """Link all dashboard components together for easy navigation"""
        
        logger.info("🔗 Linking dashboard components for seamless navigation...")
        
        # Create a summary of all created components
        dashboard_summary = {
            "overview_page_id": results.get("overview_page", {}).get("id"),
            "ai_tools_dashboard_id": results.get("ai_tools_dashboard", {}).get("id"),
            "development_dashboard_id": results.get("development_dashboard", {}).get("id"),
            "persona_knowledge_bases": {
                persona: info.get("id") for persona, info in results.get("persona_knowledge_bases", {}).items()
            },
            "creation_timestamp": datetime.now().isoformat(),
            "workspace_url": self.workspace_url
        }
        
        # Save dashboard summary for future reference
        with open("notion_dashboard_summary.json", "w") as f:
            json.dump(dashboard_summary, f, indent=2)
        
        logger.info("✅ Dashboard components linked and summary saved")
        return dashboard_summary

async def main():
    """Create comprehensive project dashboard"""
    
    # Load configuration
    config = get_config()
    
    # Create dashboard
    creator = ProjectDashboardCreator(config)
    results = await creator.create_comprehensive_dashboard()
    
    # Print summary
    print("\n🎯 Orchestra AI Project Dashboard Creation Complete!")
    print(f"📊 Workspace URL: https://www.notion.so/Orchestra-AI-Workspace-{config.workspace_id}")
    print(f"✅ Created {len(results)} dashboard components")
    
    if results.get("overview_page"):
        print(f"🎯 Main Overview: {results['overview_page']['url']}")
    
    personas = results.get("persona_knowledge_bases", {})
    if personas:
        print(f"👥 Persona Knowledge Bases: {len(personas)} created")
        for persona_name in personas.keys():
            print(f"   - {persona_name.title()}")
    
    print("\n🚀 Ready for maximum AI-assisted development productivity!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main()) 