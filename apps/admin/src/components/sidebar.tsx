"use client"

import { Link, useLocation } from "react-router-dom"
import { usePersona } from "@/contexts/PersonaContext"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { 
  Search, 
  Users, 
  Bot, 
  Settings, 
  BarChart3, 
  Shield, 
  FileText,
  Calendar,
  MessageSquare,
  Database,
  Zap,
  Network
} from "lucide-react"

interface SidebarProps {
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
}

export default function Sidebar({ sidebarOpen, setSidebarOpen }: SidebarProps) {
  const location = useLocation()
  const pathname = location.pathname
  const { activePersona, personaStates, globalMetrics } = usePersona()

  const navigationItems = [
    {
      name: "Intelligence Hub",
      href: "/intelligence-hub",
      icon: MessageSquare,
      description: "Natural Language Interface",
      badge: null
    },
    {
      name: "Data Pipeline",
      href: "/data-pipeline",
      icon: Database,
      description: "File Upload & Data Processing",
      badge: null
    },
    {
      name: "Business Tools",
      href: "/business-tools",
      icon: Settings,
      description: "API Integrations & Tool Management",
      badge: null
    },
    {
      name: "Search Center",
      href: "/",
      icon: Search,
      description: "7-Mode Search Orchestration",
      badge: personaStates[activePersona].metrics.searches > 0 ? personaStates[activePersona].metrics.searches : null
    },
    {
      name: "Agent Swarm",
      href: "/agent-swarm",
      icon: Users,
      description: "AI Agent Management",
      badge: personaStates[activePersona].metrics.activeAgents
    },
    {
      name: "Agent Factory",
      href: "/agent-factory",
      icon: Bot,
      description: "Create & Configure Agents",
      badge: null
    },
    {
      name: "AI Teams",
      href: "/ai-teams", 
      icon: Network,
      description: "Team Coordination",
      badge: null
    },
    {
      name: "Projects",
      href: "/projects",
      icon: FileText,
      description: "Project Management",
      badge: null
    },
    {
      name: "Analytics",
      href: "/analytics",
      icon: BarChart3,
      description: "Performance Insights",
      badge: null
    },
    {
      name: "Memory Store",
      href: "/memory",
      icon: Database,
      description: "Knowledge Base",
      badge: null
    },
    {
      name: "Conversations",
      href: "/conversations",
      icon: MessageSquare,
      description: "Chat History",
      badge: null
    },
    {
      name: "Automation",
      href: "/automation",
      icon: Zap,
      description: "Workflow Automation",
      badge: null
    },
    {
      name: "Schedule",
      href: "/schedule",
      icon: Calendar,
      description: "Task Scheduling",
      badge: null
    },
    {
      name: "Privacy Center",
      href: "/privacy",
      icon: Shield,
      description: "Security & Compliance",
      badge: null
    },
    {
      name: "Settings",
      href: "/settings",
      icon: Settings,
      description: "System Configuration",
      badge: null
    }
  ]

  const getPersonaColors = (persona: string) => {
    switch (persona) {
      case "cherry":
        return {
          accent: "border-red-500/50 bg-red-500/10 text-red-300",
          hover: "hover:bg-red-500/5 hover:border-red-500/30",
        }
      case "sophia":
        return {
          accent: "border-blue-500/50 bg-blue-500/10 text-blue-300",
          hover: "hover:bg-blue-500/5 hover:border-blue-500/30",
        }
      case "karen":
        return {
          accent: "border-emerald-500/50 bg-emerald-500/10 text-emerald-300",
          hover: "hover:bg-emerald-500/5 hover:border-emerald-500/30",
        }
      case "master":
        return {
          accent: "border-yellow-500/50 bg-yellow-500/10 text-yellow-300",
          hover: "hover:bg-yellow-500/5 hover:border-yellow-500/30",
        }
    }
  }

  const colors = getPersonaColors(activePersona)

  return (
    <div
      className={`fixed inset-y-0 left-0 z-40 w-64 bg-gray-900/95 backdrop-blur-md border-r border-gray-800 transform transition-transform duration-300 ease-in-out ${
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      } md:translate-x-0`}
    >
      <div className="flex flex-col h-full">
        {/* Logo/Header */}
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">🍒</span>
            <div>
              <h2 className="text-lg font-semibold text-white">Cherry AI</h2>
              <p className="text-xs text-gray-400">Orchestration Center</p>
            </div>
          </div>
        </div>

        {/* System Status */}
        <div className="p-4 border-b border-gray-800/50">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">System Load</span>
              <span className="text-xs text-white">{Math.round(globalMetrics.systemLoad * 100)}%</span>
            </div>
            <Progress value={globalMetrics.systemLoad * 100} className="h-1.5 rounded-full" />
            
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <div className="text-gray-400">Agents</div>
                <div className="text-white font-medium">{globalMetrics.totalAgents}</div>
              </div>
              <div>
                <div className="text-gray-400">Files</div>
                <div className="text-white font-medium">{globalMetrics.totalFiles}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-4 py-4">
          <div className="space-y-1">
            {navigationItems.map((item) => {
              const isActive = pathname === item.href
              const Icon = item.icon
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`group flex items-center px-3 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 ${
                    isActive
                      ? `${colors.accent} border`
                      : `text-gray-300 hover:text-white hover:bg-gray-800/50 ${colors.hover}`
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <Icon
                    className={`mr-3 h-5 w-5 transition-colors duration-200 ${
                      isActive ? "text-current" : "text-gray-400 group-hover:text-gray-300"
                    }`}
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span>{item.name}</span>
                      {item.badge && item.badge > 0 && (
                        <Badge
                          className={`ml-2 px-1.5 py-0.5 text-xs ${
                            isActive 
                              ? "bg-white/20 text-current" 
                              : "bg-gray-700 text-gray-300"
                          } rounded-full min-w-[18px] h-4 flex items-center justify-center`}
                        >
                          {item.badge}
                        </Badge>
                      )}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">{item.description}</div>
                  </div>
                </Link>
              )
            })}
          </div>
        </nav>

        {/* Persona Quick Stats */}
        <div className="p-4 border-t border-gray-800/50">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400 font-medium">
                {activePersona.charAt(0).toUpperCase() + activePersona.slice(1)} Status
              </span>
              <div className="w-2 h-2 rounded-full bg-green-500" />
            </div>
            
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-gray-800/50 rounded-lg p-2">
                <div className="text-gray-400">Active Agents</div>
                <div className="text-white font-semibold">{personaStates[activePersona].metrics.activeAgents}</div>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-2">
                <div className="text-gray-400">Searches</div>
                <div className="text-white font-semibold">{personaStates[activePersona].metrics.searches}</div>
              </div>
            </div>
            
            <div className="text-xs text-gray-500">
              Last active: {personaStates[activePersona].metrics.lastActivity.toLocaleTimeString()}
            </div>
          </div>
        </div>

        {/* Privacy Level Indicator */}
        <div className="p-4 border-t border-gray-800/50">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">Privacy Level</span>
            <Badge 
              className="text-xs px-2 py-1 rounded-md bg-blue-500/20 text-blue-400 border-blue-500/50 border"
            >
              contextual
            </Badge>
          </div>
        </div>
      </div>
    </div>
  )
} 