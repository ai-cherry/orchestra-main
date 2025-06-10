---
description: Frontend development standards for React TypeScript admin interface and dashboard
globs: ["admin-interface/**/*", "dashboard/**/*", "**/*.tsx", "**/*.ts", "**/*.jsx", "**/*.js"]
autoAttach: true
priority: high
---

# Frontend Development Standards

## React TypeScript Patterns
- **Component structure**: Functional components with TypeScript interfaces
- **Props typing**: Comprehensive TypeScript interfaces for all props
- **State management**: React Query for server state, Zustand for client state
- **Error boundaries**: Comprehensive error handling with fallback UIs
- **Code splitting**: Lazy loading for routes and heavy components

## UI/UX Excellence Standards
- **Design system**: Consistent component library with Tailwind CSS
- **Accessibility**: WCAG 2.1 AA compliance, semantic HTML, ARIA labels
- **Responsive design**: Mobile-first approach, breakpoint consistency
- **Loading states**: Skeleton screens, progressive loading, optimistic updates
- **Error handling**: User-friendly error messages, retry mechanisms

## Performance Optimization
- **Bundle optimization**: Tree-shaking, code splitting, dynamic imports
- **Rendering optimization**: useMemo, useCallback, React.memo for expensive operations
- **Image optimization**: WebP format, lazy loading, responsive images
- **Network optimization**: Request deduplication, caching strategies
- **Core Web Vitals**: LCP < 2.5s, FID < 100ms, CLS < 0.1

## State Management Patterns
- **Server state**: React Query for API data with proper cache invalidation
- **Client state**: Zustand for complex local state, React Context for simple sharing
- **Form handling**: React Hook Form with Zod validation
- **URL state**: Search params for filterable/shareable state
- **Persistence**: localStorage for user preferences, sessionStorage for temporary data

## Security and Authentication
- **JWT handling**: Secure token storage, automatic refresh, logout on expiry
- **CSRF protection**: Proper token handling, secure headers
- **XSS prevention**: Sanitize user input, use dangerouslySetInnerHTML sparingly
- **API security**: Proper CORS configuration, secure API endpoints
- **Route protection**: Role-based route guards, permission checking

## Component Architecture
- **Composition patterns**: Prefer composition over inheritance
- **Custom hooks**: Extract complex logic into reusable hooks
- **Context usage**: Avoid prop drilling, use context for cross-cutting concerns
- **Component size**: Keep components focused, split when > 200 lines
- **Naming conventions**: PascalCase for components, camelCase for functions

## Testing Standards
- **Unit testing**: React Testing Library for component testing
- **Integration testing**: API integration with MSW (Mock Service Worker)
- **E2E testing**: Playwright for critical user journeys
- **Visual testing**: Storybook for component documentation and testing
- **Accessibility testing**: axe-core integration for automated a11y testing

## Development Experience
- **Linting**: ESLint with React, TypeScript, and accessibility rules
- **Formatting**: Prettier with consistent configuration
- **Type checking**: Strict TypeScript configuration
- **Dev tools**: React DevTools, Redux DevTools integration
- **Hot reload**: Fast refresh configuration for development speed

## Build and Deployment
- **Build optimization**: Production optimizations, environment variables
- **Asset handling**: Static asset optimization, CDN integration
- **Progressive enhancement**: App works without JavaScript enabled
- **Service worker**: Caching strategies, offline functionality
- **Monitoring**: Error tracking with Sentry, performance monitoring 