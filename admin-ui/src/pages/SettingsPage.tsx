import PageWrapper from '@/components/layout/PageWrapper';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Switch } from '@/components/ui/switch';
import { useTheme } from '@/context/useTheme';
import type { Theme as AppTheme } from '@/context/ThemeContext';

const themes: { name: string; value: AppTheme }[] = [
  { name: 'Neutral', value: 'neutral' },
  { name: 'Cherry', value: 'cherry' },
  { name: 'Sophia', value: 'sophia' },
  { name: 'Gordon', value: 'gordon' }, // CSS class is 'theme-gordon'
];

export function SettingsPage() {
  const { theme, setTheme, mode, setMode } = useTheme();

  const handleThemeChange = (newThemeValue: string) => {
    const selectedTheme = themes.find(t => t.value === newThemeValue);
    if (selectedTheme) {
      setTheme(selectedTheme.value);
    }
  };

  const handleModeChange = (isDark: boolean) => {
    setMode(isDark ? 'dark' : 'light');
  };

  return (
    <PageWrapper title="Settings">
      {/* The PageWrapper already provides a main title container.
          If a secondary h1 is desired, it can be added here, but typically PageWrapper handles the main page title.
          The example had an additional h1, I'll stick to PageWrapper's title for consistency.
      */}
      {/* <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Settings</h1>
      </div> */}

      <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2"> {/* Grid for future settings sections */}
        <Card>
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
            <CardDescription>Customize the look and feel of the application.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-8"> {/* Increased spacing for better visual separation */}
            <div className="space-y-3"> {/* Slightly more spacing around label */}
              <Label className="text-base font-medium">Color Theme</Label> {/* Larger label */}
              <RadioGroup
                value={theme}
                onValueChange={handleThemeChange} // This passes the value directly
                className="pt-2 flex flex-col space-y-2" // Added pt-2 for better spacing from label
              >
                {themes.map((t) => (
                  <div key={t.value} className="flex items-center space-x-3 p-2 rounded-md hover:bg-muted transition-colors"> {/* Added hover and padding */}
                    <RadioGroupItem value={t.value} id={`theme-${t.value}`} />
                    <Label htmlFor={`theme-${t.value}`} className="font-normal cursor-pointer flex-1"> {/* Added flex-1 and cursor-pointer */}
                      {t.name}
                    </Label>
                    {/* Optional: Add a small color swatch preview */}
                    <div className={`h-5 w-5 rounded-full border border-border theme-${t.value} bg-theme-accent-primary`}></div>
                  </div>
                ))}
              </RadioGroup>
            </div>

            <div className="space-y-3">
              <Label className="text-base font-medium">Interface Mode</Label>
              <div className="flex items-center justify-between p-2 rounded-md hover:bg-muted transition-colors"> {/* Added hover and padding for consistency */}
                <Label htmlFor="dark-mode-switch" className="font-normal cursor-pointer">
                  {mode === 'dark' ? 'Dark Mode' : 'Light Mode'}
                  <p className="text-xs text-muted-foreground">
                    Switch between light and dark appearances.
                  </p>
                </Label>
                <Switch
                  id="dark-mode-switch"
                  checked={mode === 'dark'}
                  onCheckedChange={handleModeChange}
                  aria-label={`Switch to ${mode === 'dark' ? 'light' : 'dark'} mode`}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Placeholder for more settings cards */}
        {/* <Card>
          <CardHeader>
            <CardTitle>Account</CardTitle>
            <CardDescription>Manage your account settings.</CardDescription>
          </CardHeader>
          <CardContent>
            <p>Account settings form will go here.</p>
          </CardContent>
        </Card> */}
      </div>
    </PageWrapper>
  );
}
