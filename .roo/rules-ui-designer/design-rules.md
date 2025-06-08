# UI Implementation Guidelines

## Layout Principles

### 8px Grid System
- All spacing must be multiples of 8px
- Use CSS custom properties for consistent spacing:
```css
:root {
  --spacing-unit: 8px;
  --spacing-xs: calc(var(--spacing-unit) * 0.5); /* 4px */
  --spacing-sm: var(--spacing-unit);              /* 8px */
  --spacing-md: calc(var(--spacing-unit) * 2);   /* 16px */
  --spacing-lg: calc(var(--spacing-unit) * 3);   /* 24px */
  --spacing-xl: calc(var(--spacing-unit) * 4);   /* 32px */
  --spacing-2xl: calc(var(--spacing-unit) * 6);  /* 48px */
  --spacing-3xl: calc(var(--spacing-unit) * 8);  /* 64px */
}
```

### Layout Techniques
- **CSS Grid** for macro layouts (page-level structure)
- **Flexbox** for component-level arrangements
- **clamp()** for responsive typography:
  ```css
  font-size: clamp(1rem, 2.5vw, 1.5rem);
  line-height: clamp(1.4, 2vw, 1.6);
  ```

### Responsive Breakpoints (Mobile-First)
```css
/* Mobile first - no media query needed */
.container { width: 100%; }

/* Tablet */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }

/* Desktop */
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
@media (min-width: 1536px) { /* 2xl */ }
```

## Design Token Implementation

### Color System (OKLCH for Better Perceptual Uniformity)
```css
:root {
  /* Primary Colors */
  --color-primary: oklch(62.8% 0.257 255.1);
  --color-primary-hover: oklch(57.8% 0.257 255.1);
  --color-primary-active: oklch(52.8% 0.257 255.1);
  
  /* Secondary Colors */
  --color-secondary: oklch(71.2% 0.131 242.5);
  --color-secondary-hover: oklch(66.2% 0.131 242.5);
  
  /* Semantic Colors */
  --color-success: oklch(69.5% 0.149 142.4);
  --color-warning: oklch(78.9% 0.179 85.7);
  --color-error: oklch(62.9% 0.238 25.3);
  --color-info: oklch(68.8% 0.178 230.4);
  
  /* Neutral Colors */
  --color-gray-50: oklch(98.0% 0.002 247.8);
  --color-gray-100: oklch(95.9% 0.004 247.8);
  --color-gray-200: oklch(92.1% 0.008 247.8);
  --color-gray-300: oklch(86.5% 0.015 247.8);
  --color-gray-400: oklch(78.2% 0.026 247.8);
  --color-gray-500: oklch(67.8% 0.035 247.8);
  --color-gray-600: oklch(55.4% 0.042 247.8);
  --color-gray-700: oklch(44.7% 0.046 247.8);
  --color-gray-800: oklch(32.5% 0.049 247.8);
  --color-gray-900: oklch(21.5% 0.051 247.8);
}
```

### Shadow System
```css
:root {
  --shadow-xs: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-sm: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
  --shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);
  --shadow-inner: inset 0 2px 4px 0 rgb(0 0 0 / 0.05);
}
```

### Border Radius
```css
:root {
  --radius-none: 0px;
  --radius-sm: 2px;
  --radius-md: 4px;
  --radius-lg: 6px;
  --radius-xl: 8px;
  --radius-2xl: 12px;
  --radius-3xl: 16px;
  --radius-full: 9999px;
}
```

## Accessibility Enforcement (WCAG 2.2 AA)

### Required Accessibility Features
1. **All images require descriptive alt text**
   ```jsx
   <img src="chart.png" alt="Monthly sales increased by 23% from January to February 2024" />
   ```

2. **ARIA labels for all interactive elements**
   ```jsx
   <button aria-label="Close modal dialog">×</button>
   <input aria-describedby="email-error" />
   <div id="email-error" role="alert">Please enter a valid email address</div>
   ```

3. **Contrast ratios**
   - ≥ 4.5:1 for normal text (18px and below)
   - ≥ 3:1 for large text (18px+ or 14px+ bold)
   - ≥ 3:1 for UI components and graphics

4. **Focus indicators**
   ```css
   .focus-visible {
     outline: 2px solid var(--color-primary);
     outline-offset: 2px;
     border-radius: var(--radius-sm);
   }
   ```

5. **Keyboard navigation support**
   - Tab order follows logical reading sequence
   - All interactive elements reachable via keyboard
   - Skip links for main content
   - Escape key closes modals/dropdowns

6. **Screen reader compatibility**
   - Semantic HTML structure (header, nav, main, aside, footer)
   - Proper heading hierarchy (h1 → h2 → h3)
   - Form labels associated with inputs
   - Status updates announced with `aria-live`

## Performance Optimization

### CSS Containment
```css
.complex-component {
  contain: layout style paint;
}

.isolated-component {
  contain: strict;
}
```

### Dynamic Imports
```jsx
import { lazy, Suspense } from 'react';

const Chart = lazy(() => import('./Chart'));
const DataTable = lazy(() => import('./DataTable'));

function Dashboard() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Chart />
      <DataTable />
    </Suspense>
  );
}
```

### Image Optimization
```jsx
<img 
  src="/images/hero.jpg"
  alt="Team collaboration in modern office"
  loading="lazy"
  decoding="async"
  width="800"
  height="600"
/>
```

### SVG Sprites
```jsx
// sprites.svg
<svg style={{ display: 'none' }}>
  <symbol id="icon-user" viewBox="0 0 24 24">
    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
  </symbol>
</svg>

// Usage
<svg><use href="#icon-user" /></svg>
```

## Component Architecture

### Atomic Design Structure
```
src/
  components/
    atoms/
      Button/
        Button.tsx
        Button.stories.tsx
        Button.test.tsx
        index.ts
      Input/
      Icon/
      Badge/
    molecules/
      SearchBox/
      Card/
      FormGroup/
    organisms/
      Header/
      DataTable/
      LoginForm/
    templates/
      PageLayout/
      DashboardLayout/
    pages/
      HomePage/
      DashboardPage/
```

### TypeScript Interface Standards
```tsx
interface ButtonProps {
  /** Button content */
  children: React.ReactNode;
  /** Visual variant */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Disabled state */
  disabled?: boolean;
  /** Loading state */
  loading?: boolean;
  /** Click handler */
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  /** Additional CSS classes */
  className?: string;
  /** Accessibility label */
  'aria-label'?: string;
  /** Type of button */
  type?: 'button' | 'submit' | 'reset';
}
```

### Storybook Story Template
```tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Components/Atoms/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Versatile button component with multiple variants and states.'
      }
    }
  },
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['primary', 'secondary', 'outline', 'ghost']
    },
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg']
    }
  }
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: 'Button'
  }
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex gap-4">
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
    </div>
  )
};

export const AllStates: Story = {
  render: () => (
    <div className="flex gap-4 flex-col">
      <Button>Normal</Button>
      <Button disabled>Disabled</Button>
      <Button loading>Loading</Button>
    </div>
  )
};
```

## ESLint Configuration for Accessibility

```json
{
  "extends": [
    "plugin:jsx-a11y/recommended"
  ],
  "rules": {
    "jsx-a11y/alt-text": "error",
    "jsx-a11y/aria-props": "error",
    "jsx-a11y/aria-proptypes": "error",
    "jsx-a11y/aria-unsupported-elements": "error",
    "jsx-a11y/role-has-required-aria-props": "error",
    "jsx-a11y/role-supports-aria-props": "error",
    "jsx-a11y/click-events-have-key-events": "error",
    "jsx-a11y/interactive-supports-focus": "error",
    "jsx-a11y/label-has-associated-control": "error"
  }
}
```

## Quality Checklist

Before marking any UI component complete, verify:

### Design Compliance
- [ ] **8px grid alignment verified** - All spacing uses multiples of 8px
- [ ] **Design tokens used consistently** - No hardcoded colors/spacing
- [ ] **Responsive behavior confirmed** - Tests on mobile, tablet, desktop
- [ ] **Visual hierarchy clear** - Proper use of typography scale

### Accessibility
- [ ] **WCAG 2.2 AA compliance tested** - Automated and manual testing
- [ ] **Keyboard navigation works** - Tab order is logical and complete
- [ ] **Screen reader compatible** - Tested with NVDA/VoiceOver
- [ ] **Color contrast verified** - All text meets minimum ratios
- [ ] **Focus indicators visible** - Clear focus states for all interactive elements

### Performance
- [ ] **Bundle size under 250KB** - Component + dependencies
- [ ] **CSS containment applied** - For complex components
- [ ] **Images optimized** - WebP format, proper sizing, lazy loading
- [ ] **Critical CSS inlined** - Above-the-fold styles prioritized

### Code Quality
- [ ] **TypeScript errors resolved** - No any types, proper interfaces
- [ ] **ESLint jsx-a11y rules passing** - No accessibility violations
- [ ] **Storybook story created** - With comprehensive controls and examples
- [ ] **Tests written and passing** - Unit tests + accessibility tests

### Browser Compatibility
- [ ] **Cross-browser testing completed** - Chrome, Firefox, Safari, Edge
- [ ] **Mobile browsers tested** - iOS Safari, Chrome Mobile
- [ ] **Graceful degradation verified** - Works without JavaScript
- [ ] **Print styles considered** - Looks good when printed

## Common Error Codes & Solutions

| Error Code | Cause | Resolution |
|------------|-------|------------|
| E1102 | CSS Grid/Flexbox conflict | Enable `layoutValidator` plugin |
| E2045 | Missing ARIA labels | Run `a11yScanner` workflow |
| E3098 | Design token mismatch | Sync with `design-tokens.json` |
| E4011 | Browser action timeout | Increase `actionTimeout` to 45s |
| E5023 | 8px grid violation | Use spacing variables, check margins/padding |
| E6001 | Contrast ratio too low | Adjust colors to meet WCAG requirements |
| E7012 | Bundle size exceeded | Implement code splitting and lazy loading | 