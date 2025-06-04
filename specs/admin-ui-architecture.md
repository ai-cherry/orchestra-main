# Admin UI Architecture Specification

## 1. Introduction

This document outlines the architecture for the Cherry-AI Admin UI. It covers pages, routing, state management, authentication flows, and the component hierarchy. The goal is to create a modern, performant, and maintainable admin interface using React 18, Vite 5, Tailwind CSS, shadcn/ui, TanStack Router, and TanStack Query.

## 2. Pages and Routes

The following pages will be implemented, based on the existing `admin-ui/src/pages/` structure and requirements from `docs/ADMIN_IMPROVEMENT_STRATEGY.md`. Routing will be handled by TanStack Router.

| Page Name      | Route Path        | Description                                                                 | Key Features from Strategy Doc                     |
|----------------|-------------------|-----------------------------------------------------------------------------|----------------------------------------------------|
| **Dashboard**  | `/`               | Overview of system status, key metrics, and quick navigation.             | Resource usage stats, monitoring                   |
| **Agents**     | `/agents`         | Manage and monitor AI agents.                                               | Bulk actions, status indicators, pagination, creation (validation, test/preview), inline docs |
| **Personas**   | `/personas`       | Manage agent personas.                                                      | Versioning, assignment tools, preview, search/pagination |
| **Workflows**  | `/workflows`      | Define, manage, and monitor automated workflows.                            | (Details to be defined based on backend capabilities) |
| **Integrations**| `/integrations`   | Manage integrations with third-party services.                            | Modularize integration logic                       |
| **Resources**  | `/resources`      | Manage data sources, knowledge bases, or other resources used by agents.    | (Details to be defined based on backend capabilities) |
| **Logs**       | `/logs`           | View system and agent logs.                                                 | Error surfacing, filtering, search                 |
| **Settings**   | `/settings`       | Configure application settings, user management (if applicable).            | Atomic updates, validation, secrets integration, audit trail, role separation |
| **Login**      | `/login`          | User authentication page.                                                   | Secure login                                       |
| **Not Found**  | `/*` (catch-all)  | Page displayed for invalid routes.                                          |                                                    |

## 3. State Management

*   **Client-Side State:** Zustand will be used for global client-side state management (e.g., UI state, theme preferences). It's already present in the existing `admin-ui` and is lightweight.
*   **Server-Side State (Data Fetching & Caching):** TanStack Query will be used for managing server state, including data fetching, caching, synchronization, and updates. This will simplify interactions with backend APIs.

## 4. Authentication and Authorization

*   **Authentication Flow:**
    1.  User navigates to the Admin UI.
    2.  If not authenticated, user is redirected to `/login`.
    3.  User enters credentials on the Login page.
    4.  Credentials are submitted to a backend authentication API.
    5.  Upon successful authentication, a token (e.g., JWT) is returned and stored securely in the browser (e.g., HttpOnly cookie or secure local storage, TBD based on backend).
    6.  Authenticated users are redirected to the Dashboard or their intended page.
    7.  TanStack Router will handle protected routes, redirecting unauthenticated users to `/login`.
*   **Token Handling:** API requests will include the auth token in their headers.
*   **Logout:** A logout mechanism will clear the stored token and redirect the user to `/login`.
*   **Role-Based Access Control (RBAC):**
    *   The UI will adapt based on user roles provided by the backend API.
    *   Components or features might be hidden or disabled based on these roles.
    *   Specific RBAC implementation details depend on the backend API's capabilities.

## 5. Component Hierarchy (Preliminary)

A component-based architecture will be used with shadcn/ui components and custom components.

*   **Layout Components:**
    *   `AppLayout`: Main layout wrapper including Sidebar and TopBar.
    *   `Sidebar`: Navigation sidebar (collapsible, as per `figma-first-draft-prompt.txt`).
    *   `TopBar`: Top navigation bar (logo, page title, user profile, theme toggle).
    *   `PageWrapper`: Standard wrapper for page content (padding, titles).
*   **Core `shadcn/ui` Components (Examples):**
    *   `Button`, `Card`, `Table`, `Input`, `Select`, `Dialog`, `DropdownMenu`, `Tabs`, `Sheet`.
    *   These will be styled according to the Tailwind CSS configuration and design tokens.
*   **Custom Reusable Components (Examples):**
    *   `DataTable`: For displaying paginated, sortable, and filterable data (e.g., for Agents, Logs).
    *   `StatusIndicator`: Visual cue for agent status, etc.
    *   `FormWrapper`: To handle form submissions with validation (integrating with React Hook Form, often used with shadcn/ui).
    *   `MetricsDisplayCard`: For dashboard items.
*   **Page-Specific Components:**
    *   Each page (e.g., `AgentsPage`, `SettingsPage`) will compose layout components, shadcn/ui components, and custom reusable components.
    *   Example: `AgentsPage` might use `PageWrapper`, `DataTable`, `Button` (for "Create Agent").

## 6. Design System Integration

*   **Tailwind CSS:** Will be configured according to `figma-variables-spec.json` and `figma-first-draft-prompt.txt`.
*   **Design Tokens:** Color modes (Neutral, Cherry, etc.) from `figma-variables-spec.json` will be implemented using Tailwind's dark mode variants or a theme provider.
*   **Icons:** `lucide-react` will be the primary icon library, integrated with shadcn/ui components.

## 7. Conceptual Figma Frames Description (Dashboard Example)

This section provides a conceptual description of how key pages might look, serving as a guide for UI development. This is not a replacement for actual Figma designs but helps translate the architecture and design language into a visual concept.

### 7.1. Dashboard Page (Desktop - 1440px)

*   **Overall Layout:**
    *   Follows the main `AppLayout` with the dark-themed (`#111827` canvas) "tech command center aesthetic."
    *   `Sidebar` (collapsible, initial state could be collapsed to icon rail as per `figma-first-draft-prompt.txt`) on the left, using `#1F2937` surface. "Cherry" theme accent (`#E04DDA`) for active links/icons.
    *   `TopBar` (64px height) with cherry_ai logo, "Dashboard" title, user profile dropdown (using shadcn/ui `DropdownMenu`), and theme toggle.
*   **Main Content Area (12-column grid, 24px gutters, 24px padding around containers):**
    *   **Row 1: Welcome/Quick Stats (Span 12 columns)**
        *   A `Card` component (shadcn/ui) with a subtle shadow and 8px radius.
        *   Title: "Welcome, [User Name]!"
        *   Subtitle: "Overview of your Cherry-AI platform."
        *   Content: Display 3-4 key metrics as `MetricsDisplayCard` components. Each card would show:
            *   Metric Title (e.g., "Active Agents," "Workflows Running," "Resources Utilized").
            *   Value (e.g., "12", "5", "75%").
            *   A small `lucide-react` icon relevant to the metric.
            *   Use accent colors for positive/negative trends if applicable.
    *   **Row 2: Agent Status & System Health (Span 12 columns, potentially 2 cards side-by-side)**
        *   **Card 1: Agent Overview (Span 6-8 columns)**
            *   Title: "Agent Activity"
            *   Content: A compact `DataTable` (shadcn/ui `Table`) showing a few (e.g., 5) recently active agents or agents requiring attention.
                *   Columns: Agent Name, Status (using `StatusIndicator`), Last Activity.
                *   Link to `/agents` page: "View All Agents" button (shadcn/ui `Button` with primary accent).
        *   **Card 2: System Health / Logs Summary (Span 4-6 columns)**
            *   Title: "System Health" (as per `figma-first-draft-prompt.txt`)
            *   Content:
                *   Placeholder for a simple line graph (conceptual, e.g., uptime over last 24h).
                *   Key status indicators: "API Services: Healthy" (green dot), "Database Connection: Healthy" (green dot).
                *   Quick link to `/logs`: "View Detailed Logs" button (shadcn/ui `Button` with secondary accent).
    *   **Row 3: Quick Actions / Recent Activity (Span 12 columns)**
        *   A `Card` component.
        *   Title: "Quick Actions"
        *   Content: A series of `Button` components for common tasks:
            *   "Create New Agent"
            *   "Define New Workflow"
            *   "Manage Settings"
        *   Possibly a small section for "Recent Platform Activity" (e.g., "Workflow X completed", "Agent Y updated").

*   **Visual Style:**
    *   Consistent use of "Inter" font.
    *   Primary accent color (`#E04DDA` for Cherry mode) for interactive elements.
    *   Subtle grid background or dots on the main canvas if desired for depth (as per `figma-first-draft-prompt.txt`).
    *   Clear visual hierarchy using typography and spacing defined in Tailwind config.

### 7.2. Responsive Breakpoints

*   **Tablet (e.g., 768px):**
    *   Sidebar might be hidden by default, accessible via a burger menu icon in the `TopBar`.
    *   Cards in rows might stack vertically instead of side-by-side (e.g., Agent Overview and System Health).
    *   Font sizes might be slightly adjusted.
*   **Mobile (e.g., 480px):**
    *   Further stacking of elements.
    *   `DataTable` might show fewer columns or have horizontal scroll.
    *   Emphasis on touch-friendly targets for buttons and interactive elements.

This conceptual description will be expanded for other key pages as needed during development.

## 8. Migration Plan

This section details the steps to transition the existing `admin-ui/` from its current state (React 19/Vite 6/Material UI/npm, placeholder pages) to the new target architecture (React 18/Vite 5/Tailwind CSS/shadcn/ui/pnpm, functional pages based on this specification).

**Assumptions:**
*   The existing `admin-ui/` directory will be refactored in place. A full recreation (deleting and starting fresh) is also an option if it proves cleaner. This plan assumes in-place refactoring for now.
*   Backend APIs for authentication and data are either available or will be developed concurrently.

**Steps:**

1.  **Version Control:**
    *   Ensure the current state of `admin-ui/` is committed to a feature branch.

2.  **Package Manager Switch (`npm` to `pnpm`):**
    *   Delete `package-lock.json` and `node_modules/`.
    *   Install `pnpm` globally if not already available (`npm install -g pnpm`).
    *   Run `pnpm import` to attempt to generate a `pnpm-lock.yaml` from the existing `package.json`.
    *   Manually review and adjust `package.json` scripts to use `pnpm` (e.g., `pnpm dev`, `pnpm build`).

3.  **Core Dependency Version Alignment & Installation:**
    *   **React & Vite:**
        *   Modify `package.json` to specify `"react": "^18.2.0"` (or latest React 18), `"react-dom": "^18.2.0"`.
        *   Specify `"vite": "^5.0.0"` (or latest Vite 5).
        *   Remove React 19 / Vite 6 specific typings if any.
    *   **Remove Material UI:**
        *   `pnpm remove @mui/material @mui/icons-material @emotion/react @emotion/styled`.
    *   **Install New Stack:**
        *   `pnpm add tailwindcss postcss autoprefixer class-variance-authority clsx tailwind-merge lucide-react`
        *   `pnpm add -D @types/react@^18 @types/react-dom@^18` (ensure correct React 18 types)
        *   `pnpm add @tanstack/router-vite-plugin @tanstack/react-router @tanstack/react-query zustand` (Zustand is already there but ensure version compatibility).
        *   `pnpm add -D typescript@~5.4` (or latest compatible strict version)

4.  **Tailwind CSS & shadcn/ui Setup:**
    *   Initialize Tailwind CSS: `pnpm exec tailwindcss init -p`.
    *   Configure `tailwind.config.js`:
        *   Set up content paths to scan `*.tsx` files.
        *   Integrate design tokens from `figma-variables-spec.json` into `theme` (colors, fonts like "Inter").
        *   Enable dark mode (e.g., using `class` strategy).
    *   Configure `postcss.config.js` to include Tailwind CSS.
    *   Update main CSS file (e.g., `src/index.css`) to include Tailwind directives (`@tailwind base; @tailwind components; @tailwind utilities;`).
    *   Initialize shadcn/ui: `pnpm exec shadcn-ui init`.
        *   Follow prompts: Choose preferred style, base color (map from `figma-variables-spec.json`), CSS file, CSS variables, etc.
        *   This will set up `components.json` and potentially some utility files.

5.  **Application Structure Refactoring:**
    *   **Remove Old Styling:** Delete any existing CSS files or styling logic related to Material UI.
    *   **Update `src/App.tsx`:**
        *   Remove Material UI `ThemeProvider` and `CssBaseline`.
        *   Implement Tailwind's dark mode toggle if using a theme provider for it, or rely on CSS class.
        *   Replace `react-router-dom` with TanStack Router setup. (Router instance, provider, route definitions).
    *   **Refactor Core Layout Components (`Sidebar.tsx`, `TopBar.tsx`):**
        *   Rewrite these components using Tailwind CSS and shadcn/ui components (e.g., `Sheet` for sidebar, `NavigationMenu` or custom flex layout for top bar).
        *   Apply styling based on the "tech command center aesthetic" and `figma-first-draft-prompt.txt`.
    *   **Update Pages (`src/pages/*.tsx`):**
        *   Remove Material UI components from existing placeholder pages.
        *   Start implementing page structure using Tailwind CSS and shadcn/ui components as per the architecture spec and conceptual Figma descriptions.

6.  **Progressive Implementation (Iterative):**
    *   Implement one page or feature at a time (e.g., Login page, then Dashboard, then Agents).
    *   For each page:
        *   Build UI components using shadcn/ui (`pnpm exec shadcn-ui add [component-name]`) and custom components.
        *   Implement data fetching using TanStack Query.
        *   Add state management with Zustand where needed.
        *   Write Vitest unit tests.
    *   Continuously test responsiveness and accessibility.

7.  **CI/CD Adjustments:**
    *   Ensure the `.github/workflows/deploy.yaml` (or a new admin UI specific workflow if preferred) uses `pnpm install` and `pnpm build`.
    *   Verify Node.js version used in CI matches the development environment (e.g., Node 20).

8.  **Testing & QA:**
    *   Perform thorough manual testing of all pages and features.
    *   Write Playwright E2E tests for key user flows.
    *   Conduct Lighthouse audits.

9.  **Documentation:**
    *   Update any relevant READMEs or developer guides for the `admin-ui` package.

This migration plan provides a structured approach. Flexibility will be needed, and some steps might be iterative or reordered based on development discoveries.

## 9. Future Considerations

*   **Real-time Updates:** For features like agent status or logs, consider WebSocket integration (Socket.io client is in the current `admin-ui` dependencies).
*   **Internationalization (i18n):** Plan for future i18n if needed.

This specification will be updated as the project progresses.
