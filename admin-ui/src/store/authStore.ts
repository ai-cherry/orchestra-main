import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface User {
  email: string;
  // Add other user properties if needed, e.g., name, roles
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  login: (email: string, token: string) => void;
  logout: () => void;
  // initialize: () => void; // initialize can be handled by persist middleware automatically
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      user: null,
      token: null,
      login: (email, token) => {
        const userData: User = { email };
        set({ isAuthenticated: true, user: userData, token });
        console.log('User logged in:', userData);
      },
      logout: () => {
        set({ isAuthenticated: false, user: null, token: null });
        console.log('User logged out');
        // router.navigate({ to: '/login' }); // Navigation should be handled by UI components or route guards
      },
      // No explicit initialize needed if persist is used correctly;
      // it rehydrates the store on load.
    }),
    {
      name: 'admin-auth-storage', // Unique name for localStorage item
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ // Only persist these parts of the state
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        token: state.token,
      }),
    }
  )
);

// Optional: To call a function after rehydration (e.g., for debugging or initial checks)
// useAuthStore.persist.onFinishHydration((state) => {
//   console.log('Auth store rehydrated:', state);
//   // You could potentially add logic here if needed after state is loaded,
//   // for example, verifying token validity with a backend (though that's out of scope for simulated auth)
// });
