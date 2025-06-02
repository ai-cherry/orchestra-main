import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useTheme } from '@/context/useTheme';
import type { Theme } from '@/context/ThemeContext';
import { Palette, Moon, Sun, AlertTriangle } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { useNavigate } from '@tanstack/react-router'; // For navigation

// Simple Theme/Mode Toggle for Login Page
const LoginThemeToggle = () => {
  const { theme, setTheme, mode, setMode } = useTheme();
  return (
    <div className="absolute top-4 right-4 flex space-x-2">
      <select
        value={theme}
        onChange={(e) => setTheme(e.target.value as Theme)}
        className="p-2 rounded bg-muted text-foreground border border-border"
      >
        <option value="neutral">Neutral</option>
        <option value="cherry">Cherry</option>
        <option value="sophia">Sophia</option>
        <option value="gordon">Gordon</option>
      </select>
      <Button
        variant="outline"
        size="icon"
        onClick={() => setMode(mode === 'light' ? 'dark' : 'light')}
        aria-label={mode === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
      >
        {mode === 'light' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
      </Button>
    </div>
  );
};

export function LoginPage() {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuthStore();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      navigate({ to: '/' });
    }
    
    // Auto-fill credentials if remembered
    const savedCreds = localStorage.getItem('orchestra-remember');
    if (savedCreds === 'true') {
      setUsername('scoobyjava');
      setRememberMe(true);
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // Make actual API call to backend
      const apiUrl = import.meta.env.VITE_API_URL || window.location.origin;
      const response = await fetch(`${apiUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          password
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Invalid credentials');
      }

      const data = await response.json();
      
      // Save remember me preference
      if (rememberMe) {
        localStorage.setItem('orchestra-remember', 'true');
      } else {
        localStorage.removeItem('orchestra-remember');
      }
      
      // Store the token in auth store
      login(username, data.access_token || data.token);
      
      console.log('Login successful, navigating to dashboard...');
      navigate({ to: '/' });
    } catch (error) {
      console.error('Login error:', error);
      setError(error instanceof Error ? error.message : "Invalid username or password. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isAuthenticated) {
    // Render nothing or a loading indicator while redirecting
    return null;
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-background text-foreground p-4 selection:bg-theme-accent-primary selection:text-theme-accent-text">
      <LoginThemeToggle />
      <Card className="w-full max-w-md shadow-2xl">
        <CardHeader className="text-center space-y-2">
          <div className="inline-block p-3 bg-theme-accent-primary text-theme-accent-text rounded-lg mx-auto">
            <Palette size={40} />
          </div>
          <CardTitle className="text-3xl font-bold text-foreground">Admin Portal</CardTitle>
          <CardDescription className="text-muted-foreground">
            Access the Orchestra AI Management Dashboard
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-6">
            {error && (
              <div className="bg-destructive/15 p-3 rounded-md flex items-center text-sm text-destructive">
                <AlertTriangle className="h-4 w-4 mr-2" />
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="username" className="text-sm font-medium text-foreground">Username</Label>
              <Input
                id="username"
                name="username"
                type="text"
                placeholder="Enter your username"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={isLoading}
                className="w-full px-4 py-3 rounded-md border-border focus:ring-theme-accent-primary focus:border-theme-accent-primary"
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-sm font-medium text-foreground">Password</Label>
                <a href="#" className="text-xs text-theme-accent-primary hover:underline">
                  Forgot password?
                </a>
              </div>
              <Input
                id="password"
                name="password"
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                className="w-full px-4 py-3 rounded-md border-border focus:ring-theme-accent-primary focus:border-theme-accent-primary"
              />
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="remember"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-theme-accent-primary focus:ring-theme-accent-primary"
              />
              <Label htmlFor="remember" className="text-sm text-foreground">
                Remember me
              </Label>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col items-center">
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-theme-accent-primary hover:bg-opacity-85 text-theme-accent-text font-semibold py-3 rounded-md transition-colors duration-300"
            >
              {isLoading ? 'Signing In...' : 'Sign In'}
            </Button>
            <p className="mt-4 text-xs text-muted-foreground">
              &copy; {new Date().getFullYear()} Orchestra AI. All rights reserved.
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
