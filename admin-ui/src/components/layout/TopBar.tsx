import React from 'react';
import { Menu, X, Moon, Sun, User, Palette, LogOut } from 'lucide-react';
import { useTheme } from '@/context/useTheme';
import { Button } from '@/components/ui/button'; // Actual import
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu'; // Actual import
import { useAuthStore } from '@/store/authStore';
import { useNavigate, useRouterState } from '@tanstack/react-router';

interface TopBarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

const TopBar: React.FC<TopBarProps> = ({ sidebarOpen, setSidebarOpen }) => {
  const { theme, setTheme, mode, setMode } = useTheme();
  const { isAuthenticated, user, logout } = useAuthStore();
  const navigate = useNavigate();
  const routerState = useRouterState();

  const handleLogout = () => {
    logout();
    navigate({ to: '/login' });
  };

  // Attempt to get page title from router - This is a common pattern.
  // The exact way to get a "title" might depend on how routes are configured (e.g., custom route data).
  // For now, use a simple heuristic based on pathname.
  const deriveTitleFromPath = (pathname: string): string => {
    if (pathname === '/') return 'Dashboard';
    const parts = pathname.split('/').filter(Boolean);
    if (parts.length > 0) {
      return parts[parts.length - 1]
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    }
    return 'Admin'; // Default title
  };

  const currentPageTitle = deriveTitleFromPath(routerState.location.pathname);

  return (
    <header className="flex h-16 items-center justify-between bg-background border-b border-border px-4 md:px-6">
      <div className="flex items-center">
        <Button
          variant="ghost"
          size="icon"
          className="mr-2 md:hidden"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </Button>
        <span className="text-lg font-semibold ml-2 hidden md:block text-theme-accent-primary">Orchestra</span>
        <h1 className="ml-4 text-xl font-semibold text-foreground">{currentPageTitle}</h1>
      </div>

      <div className="flex items-center space-x-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" aria-label="Select Theme">
              <Palette className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {(['neutral', 'cherry', 'sophia', 'gordon'] as const).map((t) => (
              <DropdownMenuItem key={t} onClick={() => setTheme(t)} className={theme === t ? 'bg-accent text-accent-foreground' : ''}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <Button variant="ghost" size="icon" onClick={() => setMode(mode === 'light' ? 'dark' : 'light')} aria-label={mode === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}>
          {mode === 'light' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
        </Button>

        {isAuthenticated && user ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="rounded-full" aria-label="User Menu">
                <User className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem disabled className="text-sm text-muted-foreground">
                {user.email}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate({ to: '/settings' })}> {/* Example navigation */}
                Settings
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <Button variant="outline" onClick={() => navigate({ to: '/login' })}>
            Login
          </Button>
        )}
      </div>
    </header>
  );
};

export default TopBar;
