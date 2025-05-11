import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Database, 
  Users, 
  MessageSquare, 
  Network,
  Settings,
  HelpCircle
} from 'lucide-react'
import { cn } from '../../lib/utils'

/**
 * Props for the Sidebar component
 */
interface SidebarProps {
  collapsed: boolean
}

/**
 * Navigation item structure
 */
interface NavItem {
  title: string
  href: string
  icon: React.ElementType
}

/**
 * Sidebar component that provides navigation
 */
const Sidebar = ({ collapsed }: SidebarProps) => {
  const location = useLocation()
  
  const mainNavItems: NavItem[] = [
    {
      title: 'Dashboard',
      href: '/',
      icon: LayoutDashboard,
    },
    {
      title: 'Memory Management',
      href: '/memory',
      icon: Database,
    },
    {
      title: 'Agent Registry',
      href: '/agents',
      icon: Users,
    },
    {
      title: 'Conversations',
      href: '/conversations',
      icon: MessageSquare,
    },
    {
      title: 'MCP Monitoring',
      href: '/mcp',
      icon: Network,
    },
  ]

  const utilityNavItems: NavItem[] = [
    {
      title: 'Settings',
      href: '/settings',
      icon: Settings,
    },
    {
      title: 'Help',
      href: '/help',
      icon: HelpCircle,
    },
  ]

  return (
    <aside
      className={cn(
        "flex h-screen flex-col border-r bg-card transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      <div className="flex h-16 items-center border-b px-4">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            AO
          </div>
          {!collapsed && (
            <span className="text-lg font-semibold">AI Orchestra</span>
          )}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto py-4">
        <nav className="flex flex-col gap-1 px-2">
          {mainNavItems.map((item) => (
            <NavLink
              key={item.href}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )
              }
              end={item.href === '/'}
            >
              <item.icon size={20} />
              {!collapsed && <span>{item.title}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto">
          <div className="px-4 py-2">
            <div className="border-t" />
          </div>
          <nav className="flex flex-col gap-1 px-2">
            {utilityNavItems.map((item) => (
              <NavLink
                key={item.href}
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )
                }
              >
                <item.icon size={20} />
                {!collapsed && <span>{item.title}</span>}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar