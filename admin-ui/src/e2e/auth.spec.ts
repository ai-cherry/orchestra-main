import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear local storage before each test to ensure clean auth state
    // Using a specific key for auth storage as per the authStore setup
    await page.evaluate(() => localStorage.removeItem('admin-auth-storage'));
    // Navigate to login page
    await page.goto('/login');
  });

  test('should allow user to login with correct credentials', async ({ page }) => {
    // Fill in login form
    await page.getByLabel('Email Address').fill('admin@example.com'); // Matched label text from LoginPage.tsx
    await page.getByLabel('Password').fill('password');
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Assert navigation to dashboard
    await expect(page).toHaveURL('/');
    // Assert that some dashboard element is visible (TopBar title for Dashboard)
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // Assert localStorage has auth token
    const authStorage = await page.evaluate(() => localStorage.getItem('admin-auth-storage'));
    expect(authStorage).toBeTruthy();
    if (authStorage) {
      const parsedAuthStorage = JSON.parse(authStorage);
      expect(parsedAuthStorage.state.isAuthenticated).toBe(true);
      expect(parsedAuthStorage.state.user.email).toBe('admin@example.com');
      expect(parsedAuthStorage.state.token).toContain('fake-jwt-token');
    }
  });

  test('should show error message with incorrect credentials', async ({ page }) => {
    await page.getByLabel('Email Address').fill('wrong@example.com');
    await page.getByLabel('Password').fill('wrongpassword');
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Assert error message is visible
    await expect(page.getByText('Invalid email or password. Please try again.')).toBeVisible();
    // Assert still on login page
    await expect(page).toHaveURL('/login');
  });

  test('should redirect authenticated user from login to dashboard', async ({ page }) => {
    // Simulate login first
    await page.getByLabel('Email Address').fill('admin@example.com');
    await page.getByLabel('Password').fill('password');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page).toHaveURL('/');

    // Try to navigate to login page again
    await page.goto('/login');
    // Assert redirection back to dashboard (or that login page is not shown)
    // The LoginPage component itself has a useEffect to redirect if authenticated.
    await expect(page).toHaveURL('/');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should redirect unauthenticated user to login when accessing protected route', async ({ page }) => {
    await page.goto('/'); // Try to access dashboard directly
    // Assert redirection to login page
    await expect(page).toHaveURL(/\/login(\?redirect=\/)?/); // Matches /login or /login?redirect=/
  });

  test('should allow user to logout', async ({ page }) => {
    // Login first
    await page.getByLabel('Email Address').fill('admin@example.com');
    await page.getByLabel('Password').fill('password');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page).toHaveURL('/');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // Click user menu button (assuming it's a button with aria-label or specific role)
    await page.getByRole('button', { name: 'User Menu' }).click(); // From TopBar.tsx aria-label

    // Click logout button
    await page.getByRole('menuitem', { name: 'Logout' }).click(); // From TopBar.tsx DropdownMenuItem

    // Assert navigation to login page
    await expect(page).toHaveURL('/login');

    // Assert localStorage reflects logged out state
    const authStorage = await page.evaluate(() => localStorage.getItem('admin-auth-storage'));
    expect(authStorage).toBeTruthy();
    if (authStorage) {
      const parsedAuthStorage = JSON.parse(authStorage);
      expect(parsedAuthStorage.state.isAuthenticated).toBe(false);
      expect(parsedAuthStorage.state.token).toBeNull();
      expect(parsedAuthStorage.state.user).toBeNull();
    }
  });
});
