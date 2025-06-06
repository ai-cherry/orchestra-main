import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { 
  LayoutDashboard, 
  Users, 
  Search, 
  Workflow, 
  Palette, 
  Monitor,
  ChevronLeft,
  ChevronRight,
  Heart,
  Briefcase,
  Stethoscope
} from 'lucide-react'

const navigationItems = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    description: 'System overview and metrics'
  },
  {
    title: 'Personas',
    href: '/personas',
    icon: Users,
    description: 'Cherry, Sophia, Karen management',
    subItems: [
      { title: 'Cherry', href: '/personas/cherry', icon: Heart, color: 'text-pink-500' },
      { title: 'Sophia', href: '/personas/sophia', icon: Briefcase, color: 'text-blue-500' },
      { title: 'Karen', href: '/personas/karen', icon: Stethoscope, color: 'text-green-500' }
    ]
  },
  {
    title: 'Search Center',
    href: '/search',
    icon: Search,
    description: 'Multi-modal search and discovery'
  },
  {
    title: 'Workflows',
    href: '/workflows',
    icon: Workflow,
    description: 'Visual workflow builder and automation'
  },
  {
    title: 'Generate',
    href: '/generate',
    icon: Palette,
    description: 'Multi-modal content generation'
  },
  {
    title: 'System Monitor',
    href: '/system',
    icon: Monitor,
    description: 'Performance and health monitoring'
  }
]

export function Sidebar({ collapsed, onToggle }) {
  const location = useLocation()
  const [expandedItems, setExpandedItems] = useState(['Personas'])

  const toggleExpanded = (title) => {
    setExpandedItems(prev => 
      prev.includes(title) 
        ? prev.filter(item => item !== title)
        : [...prev, title]
    )
  }

  const isActive = (href) => {
    if (href === '/dashboard' && location.pathname === '/') return true
    return location.pathname.startsWith(href)
  }

  return (
    <div className={cn(
      "bg-sidebar border-r border-sidebar-border transition-all duration-300 ease-in-out flex flex-col",
      collapsed ? "w-16" : "w-64"
    )}>
      {/* Header */}
      <div className="p-4 border-b border-sidebar-border">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <div>
              <h1 className="text-lg font-semibold text-sidebar-foreground">
                AI Admin
              </h1>
              <p className="text-sm text-sidebar-foreground/60">
                Mission Control
              </p>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggle}
            className="text-sidebar-foreground hover:bg-sidebar-accent"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1">
        {navigationItems.map((item) => (
          <div key={item.title}>
            <Link
              to={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                isActive(item.href) 
                  ? "bg-sidebar-accent text-sidebar-accent-foreground" 
                  : "text-sidebar-foreground"
              )}
              onClick={() => item.subItems && toggleExpanded(item.title)}
            >
              <item.icon className="h-4 w-4 flex-shrink-0" />
              {!collapsed && (
                <>
                  <span className="flex-1">{item.title}</span>
                  {item.subItems && (
                    <ChevronRight 
                      className={cn(
                        "h-4 w-4 transition-transform",
                        expandedItems.includes(item.title) && "rotate-90"
                      )} 
                    />
                  )}
                </>
              )}
            </Link>

            {/* Sub-items */}
            {!collapsed && item.subItems && expandedItems.includes(item.title) && (
              <div className="ml-6 mt-1 space-y-1">
                {item.subItems.map((subItem) => (
                  <Link
                    key={subItem.href}
                    to={subItem.href}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                      "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                      isActive(subItem.href)
                        ? "bg-sidebar-accent text-sidebar-accent-foreground"
                        : "text-sidebar-foreground/80"
                    )}
                  >
                    <subItem.icon className={cn("h-4 w-4 flex-shrink-0", subItem.color)} />
                    <span>{subItem.title}</span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-sidebar-border">
          <div className="text-xs text-sidebar-foreground/60">
            <p>AI Assistant Ecosystem</p>
            <p>Version 2.0.0</p>
          </div>
        </div>
      )}
    </div>
  )
}

