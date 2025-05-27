# Admin UI Smoke Test Plan

This document outlines a set of manual smoke tests to be performed against a deployed instance of the Admin UI (e.g., on the staging/dev environment).

**Target URL:** (To be filled in with the deployed `admin_ui_live_url` or `admin_ui_default_url`)

**Pre-requisites:**
*   Admin UI has been successfully deployed.
*   Known test user credentials (e.g., `admin@example.com` / `password` as per simulated auth).

**Test Cases:**

1.  **TC01: Load Login Page**
    *   **Steps:** Navigate to the Admin UI base URL.
    *   **Expected Result:** Should be redirected to the `/login` page. The login form is displayed correctly. Theme (colors, fonts) is applied.
    *   **Status:** Pass/Fail

2.  **TC02: Invalid Login Attempt**
    *   **Steps:**
        1.  On the Login page, enter incorrect credentials (e.g., `wrong@example.com` / `wrongpassword`).
        2.  Click "Sign In".
    *   **Expected Result:** An error message "Invalid email or password" (or similar) is displayed. User remains on the `/login` page.
    *   **Status:** Pass/Fail

3.  **TC03: Valid Login**
    *   **Steps:**
        1.  On the Login page, enter valid credentials (`admin@example.com` / `password`).
        2.  Click "Sign In".
    *   **Expected Result:** User is redirected to the Dashboard (`/`). The main application layout (Sidebar, TopBar) is visible. User's email is displayed in the TopBar.
    *   **Status:** Pass/Fail

4.  **TC04: Navigate to Dashboard**
    *   **Steps:** (Assuming user is logged in) If not on Dashboard, click "Dashboard" in Sidebar.
    *   **Expected Result:** Dashboard page content is displayed correctly, including welcome message, metrics cards, agent activity, system health, and quick actions sections. Mock data is visible.
    *   **Status:** Pass/Fail

5.  **TC05: Navigate to Agents Page**
    *   **Steps:** Click "Agents" in Sidebar.
    *   **Expected Result:** Agents page is displayed. "Create Agent" button is visible. Table of mock agents is displayed with correct columns (Name, Status, Last Updated, Actions). Dropdown actions are present for each agent.
    *   **Status:** Pass/Fail

6.  **TC06: Navigate to Personas Page**
    *   **Steps:** Click "Personas" in Sidebar.
    *   **Expected Result:** Personas page is displayed. "Create Persona" button is visible. Table of mock personas is displayed with correct columns. Dropdown actions are present.
    *   **Status:** Pass/Fail

7.  **TC07: Navigate to Logs Page**
    *   **Steps:** Click "Logs" in Sidebar.
    *   **Expected Result:** Logs page is displayed. Filter/search controls are present. Table of mock logs is displayed with correct columns (Timestamp, Level, Source, Message).
    *   **Status:** Pass/Fail

8.  **TC08: Navigate to Integrations Page**
    *   **Steps:** Click "Integrations" in Sidebar.
    *   **Expected Result:** Integrations page is displayed. "Add New Integration" button is visible. Grid of mock integration cards is displayed with name, icon, status, description, and action buttons.
    *   **Status:** Pass/Fail

9.  **TC09: Navigate to Workflows Page**
    *   **Steps:** Click "Workflows" in Sidebar.
    *   **Expected Result:** Workflows page is displayed. "Create Workflow" button is visible. Table of mock workflows is displayed with correct columns. Dropdown actions are present.
    *   **Status:** Pass/Fail

10. **TC10: Navigate to Resources Page**
    *   **Steps:** Click "Resources" in Sidebar.
    *   **Expected Result:** Resources page is displayed. "Add Resource" button is visible. Table of mock resources is displayed with correct columns (Type icon, Name, Size, Date Added, Status, Actions). Dropdown actions are present.
    *   **Status:** Pass/Fail

11. **TC11: Theme and Mode Toggle on Settings Page**
    *   **Steps:**
        1.  Navigate to the Settings page.
        2.  Select a different Color Theme (e.g., "Cherry").
        3.  Toggle the Interface Mode (e.g., to Dark Mode if currently Light).
    *   **Expected Result:**
        1.  The application's color scheme updates immediately to reflect the selected theme.
        2.  The application switches between light and dark mode correctly.
        3.  These settings should persist if the user navigates to another page and back (due to ThemeContext and localStorage).
    *   **Status:** Pass/Fail

12. **TC12: Logout**
    *   **Steps:** Click the "Logout" button in the TopBar.
    *   **Expected Result:** User is redirected to the `/login` page. Accessing a protected route (e.g., `/`) should redirect back to `/login`.
    *   **Status:** Pass/Fail

13. **TC13: Responsive Check (Brief)**
    *   **Steps:**
        1.  On a key page like Dashboard or Agents, resize browser window to simulate tablet/mobile views.
    *   **Expected Result:** Layout adjusts appropriately. Tables are scrollable if content overflows. Sidebar collapses or becomes an overlay. No major visual breakage.
    *   **Status:** Pass/Fail

**End of Smoke Test.**
