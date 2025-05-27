import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from './authStore'; // Adjust path as needed

// Define the initial state structure for resetting
const initialAuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
};

describe('useAuthStore', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useAuthStore.setState(initialAuthState, true); // `true` replaces the entire state

    // Clear localStorage for the specific item to ensure a clean slate for persist middleware
    // This is important because `persist` middleware will rehydrate from localStorage.
    localStorage.removeItem('admin-auth-storage');

    // Optional: If you need to re-trigger rehydration manually after clearing localStorage for some reason
    // (though usually not needed if tests set state directly or if the store rehydrates on first access/import).
    // await useAuthStore.persist.rehydrate(); // This might be needed if your tests rely on initial load behavior
  });

  it('should have correct initial state', () => {
    const { isAuthenticated, user, token } = useAuthStore.getState();
    expect(isAuthenticated).toBe(false);
    expect(user).toBeNull();
    expect(token).toBeNull();
  });

  it('should update state on login', () => {
    const testEmail = 'test@example.com';
    const testToken = 'test-token-123';

    // Spy on console.log to check if it's called during login
    const consoleSpy = vi.spyOn(console, 'log');

    act(() => {
      useAuthStore.getState().login(testEmail, testToken);
    });

    const { isAuthenticated, user, token } = useAuthStore.getState();
    expect(isAuthenticated).toBe(true);
    expect(user).toEqual({ email: testEmail });
    expect(token).toBe(testToken);
    expect(consoleSpy).toHaveBeenCalledWith('User logged in:', { email: testEmail });

    consoleSpy.mockRestore(); // Clean up spy
  });

  it('should reset state on logout', () => {
    const testEmail = 'test@example.com';
    const testToken = 'test-token-123';

    // Spy on console.log
    const consoleSpy = vi.spyOn(console, 'log');

    // First login
    act(() => {
      useAuthStore.getState().login(testEmail, testToken);
    });

    // Then logout
    act(() => {
      useAuthStore.getState().logout();
    });

    const { isAuthenticated, user, token } = useAuthStore.getState();
    expect(isAuthenticated).toBe(false);
    expect(user).toBeNull();
    expect(token).toBeNull();
    expect(consoleSpy).toHaveBeenCalledWith('User logged out');

    consoleSpy.mockRestore(); // Clean up spy
  });

  it('should persist state to localStorage on login and clear on logout', async () => {
    const testEmail = 'test@example.com';
    const testToken = 'test-token-xyz';

    act(() => {
      useAuthStore.getState().login(testEmail, testToken);
    });

    // Zustand persist middleware might save asynchronously, so wait for changes
    await vi.waitFor(() => {
      const storedStateRaw = localStorage.getItem('admin-auth-storage');
      expect(storedStateRaw).not.toBeNull();
      if (storedStateRaw) {
        const storedState = JSON.parse(storedStateRaw);
        expect(storedState.state.isAuthenticated).toBe(true);
        expect(storedState.state.user.email).toBe(testEmail);
        expect(storedState.state.token).toBe(testToken);
      }
    });

    act(() => {
      useAuthStore.getState().logout();
    });

    await vi.waitFor(() => {
      const storedStateRaw = localStorage.getItem('admin-auth-storage');
      expect(storedStateRaw).not.toBeNull();
      if (storedStateRaw) {
        const storedState = JSON.parse(storedStateRaw);
        expect(storedState.state.isAuthenticated).toBe(false);
        expect(storedState.state.user).toBeNull();
        expect(storedState.state.token).toBeNull();
      }
    });
  });
});

// Helper for wrapping state updates in tests if you encounter issues with React updates
// For Zustand outside of React components, direct calls are usually fine, but if used
// with hooks that trigger React updates, 'act' might be needed.
// Vitest's environment might handle this, but it's good to be aware of.
function act(callback: () => void) {
  callback();
}
