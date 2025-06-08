# UI Designer Standards and Guidelines

## Overview
This document defines the design standards, patterns, and practices for the UI Designer mode in Project Symphony: AI Orchestra. These guidelines ensure consistent, accessible, and high-quality user interface development.

## Atomic Design Principles

### Design System Hierarchy
```
Pages (Ecosystems)
  ↓
Templates (Templates) 
  ↓
Organisms (Complex Components)
  ↓
Molecules (Simple Components)
  ↓
Atoms (Basic Elements)
  ↓
Tokens (Design Variables)
```

### Component Categories

#### Atoms
- Input fields, buttons, labels, icons
- Typography elements (headings, paragraphs)
- Basic form controls
- Loading indicators

#### Molecules  
- Search forms, navigation items
- Card headers, media objects
- Form groups with labels and validation

#### Organisms
- Headers, footers, navigation bars
- Article cards, product cards
- Complex forms, data tables

#### Templates
- Page layouts without content
- Grid systems and spacing
- Content flow patterns

#### Pages
- Specific instances with real content
- User flows and interactions
- Complete user experiences

## Accessibility Standards (WCAG 2.2 AA)

### Required Compliance Checks
- [ ] **Keyboard Navigation**: All interactive elements accessible via keyboard
- [ ] **Screen Reader Support**: Proper ARIA labels, roles, and properties
- [ ] **Color Contrast**: Minimum 4.5:1 ratio for normal text, 3:1 for large text
- [ ] **Focus Management**: Visible focus indicators and logical tab order
- [ ] **Alternative Text**: Descriptive alt text for all images
- [ ] **Form Labels**: Explicit labels for all form controls
- [ ] **Error Handling**: Clear, accessible error messages
- [ ] **Responsive Design**: Works on all screen sizes and orientations

### Accessibility Testing Tools
```bash
# Automated testing
npm run test:a11y
npm run lighthouse:a11y

# Manual testing checklist
- Keyboard-only navigation test
- Screen reader testing (NVDA/JAWS)
- Color blindness simulation
- High contrast mode testing
```

## CSS-in-JS with Emotion

### Styled Components Pattern
```jsx
import styled from '@emotion/styled'
import { css } from '@emotion/react'

// Base component with design tokens
const Button = styled.button`
  ${({ theme, variant = 'primary', size = 'medium' }) => css`
    padding: ${theme.spacing[size]};
    background-color: ${theme.colors[variant]};
    border-radius: ${theme.radii.medium};
    font-family: ${theme.fonts.body};
    transition: ${theme.transitions.fast};
    
    &:hover {
      background-color: ${theme.colors[`${variant}Hover`]};
    }
    
    &:focus {
      outline: 2px solid ${theme.colors.focus};
      outline-offset: 2px;
    }
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  `}
`
```

### Design Token Integration
```javascript
// theme.js
export const theme = {
  colors: {
    primary: '#0066CC',
    primaryHover: '#0052A3', 
    secondary: '#6C757D',
    success: '#28A745',
    warning: '#FFC107',
    danger: '#DC3545',
    focus: '#80BDFF'
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem', 
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem'
  },
  typography: {
    fontSizes: {
      xs: '0.75rem',
      sm: '0.875rem',
      md: '1rem',
      lg: '1.25rem',
      xl: '1.5rem'
    },
    lineHeights: {
      tight: 1.2,
      normal: 1.5,
      loose: 1.8
    }
  },
  breakpoints: {
    sm: '640px',
    md: '768px', 
    lg: '1024px',
    xl: '1280px'
  }
}
```

## Mobile-First Responsive Design

### Breakpoint Strategy
```scss
// Mobile first approach
.component {
  // Base mobile styles
  padding: 1rem;
  
  // Tablet and up
  @media (min-width: 768px) {
    padding: 1.5rem;
  }
  
  // Desktop and up  
  @media (min-width: 1024px) {
    padding: 2rem;
  }
}
```

### Responsive Component Patterns
```jsx
const ResponsiveGrid = styled.div`
  display: grid;
  gap: 1rem;
  grid-template-columns: 1fr;
  
  @media (min-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
  }
  
  @media (min-width: 1024px) {
    grid-template-columns: repeat(3, 1fr);
  }
`
```

## Storybook Integration

### Story Structure
```javascript
// Button.stories.js
export default {
  title: 'Components/Atoms/Button',
  component: Button,
  parameters: {
    docs: {
      description: {
        component: 'Primary button component with multiple variants and states'
      }
    }
  },
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['primary', 'secondary', 'danger']
    },
    size: {
      control: { type: 'select' },
      options: ['small', 'medium', 'large']
    }
  }
}

export const Primary = {
  args: {
    variant: 'primary',
    children: 'Primary Button'
  }
}

export const AllStates = () => (
  <div style={{ display: 'flex', gap: '1rem', flexDirection: 'column' }}>
    <Button variant="primary">Normal</Button>
    <Button variant="primary" disabled>Disabled</Button>
    <Button variant="primary" aria-pressed="true">Pressed</Button>
  </div>
)
```

### Required Story Types
- **Default**: Basic component usage
- **All Variants**: All visual variations
- **All States**: Hover, focus, disabled, active
- **Responsive**: Different screen sizes
- **Accessibility**: Keyboard navigation demo
- **Dark Mode**: Theme variations

## Performance Optimization

### Bundle Size Guidelines
- **Individual Components**: < 5KB gzipped
- **Page Bundle**: < 250KB initial load
- **Total Bundle**: < 1MB for entire app
- **Critical CSS**: < 50KB above-the-fold

### Optimization Techniques
```javascript
// Code splitting for large components
const LazyChart = lazy(() => import('./Chart'))

// Memoization for expensive renders
const OptimizedComponent = memo(({ data }) => {
  const processedData = useMemo(() => 
    expensiveDataProcessing(data), [data]
  )
  
  return <Chart data={processedData} />
})

// Image optimization
const OptimizedImage = ({ src, alt, ...props }) => (
  <img 
    src={src}
    alt={alt}
    loading="lazy"
    decoding="async"
    {...props}
  />
)
```

## Component API Design

### Prop Conventions
```typescript
interface ComponentProps {
  // Visual variants
  variant?: 'primary' | 'secondary' | 'danger'
  size?: 'small' | 'medium' | 'large'
  
  // State
  disabled?: boolean
  loading?: boolean
  
  // Content
  children: React.ReactNode
  
  // Accessibility
  'aria-label'?: string
  'aria-describedby'?: string
  
  // Styling
  className?: string
  style?: React.CSSProperties
  
  // Events
  onClick?: (event: React.MouseEvent) => void
}
```

### Documentation Requirements
- [ ] **TypeScript interfaces** for all props
- [ ] **JSDoc comments** for complex props
- [ ] **Usage examples** in component file
- [ ] **Storybook documentation** with controls
- [ ] **Accessibility notes** for screen readers
- [ ] **Performance considerations** if applicable

## Testing Standards

### Component Testing
```javascript
import { render, screen, userEvent } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'

expect.extend(toHaveNoViolations)

test('Button renders correctly', () => {
  render(<Button>Click me</Button>)
  expect(screen.getByRole('button')).toBeInTheDocument()
})

test('Button is accessible', async () => {
  const { container } = render(<Button>Click me</Button>)
  const results = await axe(container)
  expect(results).toHaveNoViolations()
})

test('Button handles interactions', async () => {
  const handleClick = jest.fn()
  render(<Button onClick={handleClick}>Click me</Button>)
  
  await userEvent.click(screen.getByRole('button'))
  expect(handleClick).toHaveBeenCalledTimes(1)
})
```

## Quality Checklist

Before marking any UI component complete, verify:

### Design Compliance
- [ ] Follows atomic design principles
- [ ] Uses design tokens consistently  
- [ ] Matches design system specifications
- [ ] Responsive across all breakpoints

### Accessibility
- [ ] WCAG 2.2 AA compliant
- [ ] Keyboard accessible
- [ ] Screen reader tested
- [ ] Color contrast verified

### Performance
- [ ] Bundle size within limits
- [ ] Images optimized
- [ ] Code split appropriately
- [ ] Renders efficiently

### Documentation
- [ ] Storybook stories complete
- [ ] TypeScript types defined
- [ ] Usage examples provided
- [ ] Accessibility notes included

### Testing
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Accessibility tests passing
- [ ] Visual regression tests passing 