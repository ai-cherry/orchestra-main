import React, { useState } from 'react';
import { 
  OrchestraButton 
} from '@/components/ui/OrchestraButton';
import { 
  OrchestraCard,
  CardHeader,
  CardContent,
  CardTitle,
  CardDescription,
  StatCard
} from '@/components/ui/OrchestraCard';

// Mock icons (replace with your preferred icon library)
const UserIcon = () => (
  <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
  </svg>
);

const ChartIcon = () => (
  <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const CpuIcon = () => (
  <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
  </svg>
);

export const DesignSystemDemo: React.FC = () => {
  const [loading, setLoading] = useState(false);

  const handleLoadingDemo = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 2000);
  };

  return (
    <div className="min-h-screen bg-orchestra-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-orchestra-gray-900 mb-2">
            🎼 Orchestra AI Design System
          </h1>
          <p className="text-lg text-orchestra-gray-600">
            A comprehensive design system demo showcasing Orchestra AI's UI components and patterns.
          </p>
        </div>

        {/* Color Palette Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-orchestra-gray-900 mb-6">Color Palette</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <div className="text-center">
              <div className="w-full h-16 bg-orchestra-primary rounded-lg mb-2"></div>
              <p className="text-sm font-medium">Primary</p>
              <p className="text-xs text-orchestra-gray-500">#2563eb</p>
            </div>
            <div className="text-center">
              <div className="w-full h-16 bg-orchestra-secondary rounded-lg mb-2"></div>
              <p className="text-sm font-medium">Secondary</p>
              <p className="text-xs text-orchestra-gray-500">#7c3aed</p>
            </div>
            <div className="text-center">
              <div className="w-full h-16 bg-orchestra-accent rounded-lg mb-2"></div>
              <p className="text-sm font-medium">Accent</p>
              <p className="text-xs text-orchestra-gray-500">#059669</p>
            </div>
            <div className="text-center">
              <div className="w-full h-16 bg-orchestra-warning rounded-lg mb-2"></div>
              <p className="text-sm font-medium">Warning</p>
              <p className="text-xs text-orchestra-gray-500">#d97706</p>
            </div>
            <div className="text-center">
              <div className="w-full h-16 bg-orchestra-error rounded-lg mb-2"></div>
              <p className="text-sm font-medium">Error</p>
              <p className="text-xs text-orchestra-gray-500">#dc2626</p>
            </div>
            <div className="text-center">
              <div className="w-full h-16 bg-orchestra-gray-400 rounded-lg mb-2"></div>
              <p className="text-sm font-medium">Gray</p>
              <p className="text-xs text-orchestra-gray-500">#9ca3af</p>
            </div>
          </div>
        </section>

        {/* Buttons Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-orchestra-gray-900 mb-6">Buttons</h2>
          <div className="space-y-6">
            {/* Button Variants */}
            <div>
              <h3 className="text-lg font-medium text-orchestra-gray-800 mb-4">Variants</h3>
              <div className="flex flex-wrap gap-4">
                <OrchestraButton variant="primary">Primary Button</OrchestraButton>
                <OrchestraButton variant="secondary">Secondary Button</OrchestraButton>
                <OrchestraButton variant="ghost">Ghost Button</OrchestraButton>
                <OrchestraButton variant="success">Success Button</OrchestraButton>
                <OrchestraButton variant="danger">Danger Button</OrchestraButton>
              </div>
            </div>

            {/* Button Sizes */}
            <div>
              <h3 className="text-lg font-medium text-orchestra-gray-800 mb-4">Sizes</h3>
              <div className="flex flex-wrap items-center gap-4">
                <OrchestraButton size="sm">Small</OrchestraButton>
                <OrchestraButton size="md">Medium</OrchestraButton>
                <OrchestraButton size="lg">Large</OrchestraButton>
                <OrchestraButton size="xl">Extra Large</OrchestraButton>
              </div>
            </div>

            {/* Button States */}
            <div>
              <h3 className="text-lg font-medium text-orchestra-gray-800 mb-4">States</h3>
              <div className="flex flex-wrap gap-4">
                <OrchestraButton variant="primary">Normal</OrchestraButton>
                <OrchestraButton variant="primary" loading={loading} onClick={handleLoadingDemo}>
                  {loading ? 'Loading...' : 'Click for Loading State'}
                </OrchestraButton>
                <OrchestraButton variant="primary" disabled>Disabled</OrchestraButton>
              </div>
            </div>
          </div>
        </section>

        {/* Cards Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-orchestra-gray-900 mb-6">Cards</h2>
          
          {/* Stat Cards */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-orchestra-gray-800 mb-4">Stat Cards</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <StatCard
                title="Total Users"
                value="1,234"
                icon={<UserIcon />}
                trend={{ value: 12.5, isPositive: true }}
              />
              <StatCard
                title="Revenue"
                value="$45.2K"
                icon={<ChartIcon />}
                trend={{ value: 8.2, isPositive: true }}
              />
              <StatCard
                title="Server Load"
                value="67%"
                icon={<CpuIcon />}
                trend={{ value: 3.1, isPositive: false }}
              />
            </div>
          </div>

          {/* Feature Cards */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-orchestra-gray-800 mb-4">Feature Cards</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <OrchestraCard variant="feature">
                <CardHeader>
                  <CardTitle>Memory Management</CardTitle>
                  <CardDescription>
                    Advanced memory management with intelligent caching and persistence.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm text-orchestra-gray-600">
                    <li>• Real-time memory optimization</li>
                    <li>• Automatic garbage collection</li>
                    <li>• Context-aware caching</li>
                  </ul>
                  <div className="mt-4">
                    <OrchestraButton size="sm" variant="primary">Learn More</OrchestraButton>
                  </div>
                </CardContent>
              </OrchestraCard>

              <OrchestraCard variant="feature">
                <CardHeader>
                  <CardTitle>Agent Coordination</CardTitle>
                  <CardDescription>
                    Seamless multi-agent communication and task orchestration.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm text-orchestra-gray-600">
                    <li>• Multi-agent workflows</li>
                    <li>• Task delegation</li>
                    <li>• Conflict resolution</li>
                  </ul>
                  <div className="mt-4">
                    <OrchestraButton size="sm" variant="secondary">Learn More</OrchestraButton>
                  </div>
                </CardContent>
              </OrchestraCard>

              <OrchestraCard variant="feature">
                <CardHeader>
                  <CardTitle>Data Integration</CardTitle>
                  <CardDescription>
                    Connect and synchronize data from multiple sources seamlessly.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm text-orchestra-gray-600">
                    <li>• Real-time data sync</li>
                    <li>• Multiple connectors</li>
                    <li>• Data transformation</li>
                  </ul>
                  <div className="mt-4">
                    <OrchestraButton size="sm" variant="ghost">Learn More</OrchestraButton>
                  </div>
                </CardContent>
              </OrchestraCard>
            </div>
          </div>

          {/* Glass Card */}
          <div>
            <h3 className="text-lg font-medium text-orchestra-gray-800 mb-4">Glass Effect Card</h3>
            <div className="relative">
              {/* Background image or pattern */}
              <div className="absolute inset-0 bg-gradient-to-br from-orchestra-primary to-orchestra-secondary rounded-lg"></div>
              <div className="relative p-6">
                <OrchestraCard variant="glass" className="max-w-md">
                  <CardContent>
                    <h3 className="text-lg font-semibold text-orchestra-gray-900 mb-2">
                      Glass Morphism Card
                    </h3>
                    <p className="text-orchestra-gray-600 mb-4">
                      This card demonstrates the glass morphism effect with backdrop blur and transparency.
                    </p>
                    <OrchestraButton size="sm" variant="primary">
                      Explore
                    </OrchestraButton>
                  </CardContent>
                </OrchestraCard>
              </div>
            </div>
          </div>
        </section>

        {/* Typography Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-orchestra-gray-900 mb-6">Typography</h2>
          <OrchestraCard>
            <CardContent>
              <div className="space-y-4">
                <h1 className="text-6xl font-bold text-orchestra-gray-900">Heading 1</h1>
                <h2 className="text-5xl font-bold text-orchestra-gray-900">Heading 2</h2>
                <h3 className="text-4xl font-semibold text-orchestra-gray-900">Heading 3</h3>
                <h4 className="text-3xl font-semibold text-orchestra-gray-900">Heading 4</h4>
                <h5 className="text-2xl font-medium text-orchestra-gray-900">Heading 5</h5>
                <h6 className="text-xl font-medium text-orchestra-gray-900">Heading 6</h6>
                <p className="text-base text-orchestra-gray-700 max-w-2xl">
                  This is body text. Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
                  Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad 
                  minim veniam, quis nostrud exercitation ullamco laboris.
                </p>
                <p className="text-sm text-orchestra-gray-600">Small text for captions and metadata.</p>
                <code className="text-sm font-mono bg-orchestra-gray-100 px-2 py-1 rounded">
                  console.log('Monospace code text');
                </code>
              </div>
            </CardContent>
          </OrchestraCard>
        </section>

        {/* Accessibility Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-orchestra-gray-900 mb-6">Accessibility Features</h2>
          <OrchestraCard>
            <CardContent>
              <div className="space-y-4">
                <p className="text-orchestra-gray-700">
                  The Orchestra AI design system includes comprehensive accessibility features:
                </p>
                <ul className="space-y-2 text-orchestra-gray-600">
                  <li>• Keyboard navigation support (try tabbing through buttons)</li>
                  <li>• Focus indicators with proper contrast ratios</li>
                  <li>• ARIA labels and semantic HTML structure</li>
                  <li>• Screen reader compatible components</li>
                  <li>• Color contrast ratios meeting WCAG 2.1 AA standards</li>
                </ul>
                <div className="flex gap-4 mt-6">
                  <OrchestraButton variant="primary" tabIndex={0}>
                    Tab-accessible Button 1
                  </OrchestraButton>
                  <OrchestraButton variant="secondary" tabIndex={0}>
                    Tab-accessible Button 2
                  </OrchestraButton>
                  <OrchestraButton variant="ghost" tabIndex={0}>
                    Tab-accessible Button 3
                  </OrchestraButton>
                </div>
              </div>
            </CardContent>
          </OrchestraCard>
        </section>

        {/* Usage Instructions */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-orchestra-gray-900 mb-6">How to Use This Design System</h2>
          <OrchestraCard>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-orchestra-gray-900 mb-2">1. Import Components</h3>
                  <code className="block text-sm font-mono bg-orchestra-gray-100 p-4 rounded">
                    {`import { OrchestraButton } from '@/components/ui/OrchestraButton';
import { OrchestraCard, CardHeader, CardContent } from '@/components/ui/OrchestraCard';`}
                  </code>
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold text-orchestra-gray-900 mb-2">2. Use Design Tokens</h3>
                  <code className="block text-sm font-mono bg-orchestra-gray-100 p-4 rounded">
                    {`<div className="bg-orchestra-primary text-white p-4">
  Using Orchestra AI colors
</div>`}
                  </code>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-orchestra-gray-900 mb-2">3. Follow Patterns</h3>
                  <p className="text-orchestra-gray-700">
                    Reference the <code>/.cursor/agents/ui_designer_agent.md</code> file for comprehensive 
                    patterns, guidelines, and best practices.
                  </p>
                </div>
              </div>
            </CardContent>
          </OrchestraCard>
        </section>
      </div>
    </div>
  );
}; 