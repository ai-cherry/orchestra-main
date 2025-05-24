import * as React from "react";

import type { ToastActionElement, ToastProps } from "./toast";

/**
 * Toast state type
 */
type ToasterToast = ToastProps & {
  id: string;
  title?: React.ReactNode;
  description?: React.ReactNode;
  action?: ToastActionElement;
};

/**
 * Toast context type
 */
type ToastContext = {
  toasts: ToasterToast[];
  add: (toast: Omit<ToasterToast, "id">) => void;
  update: (id: string, toast: Partial<ToasterToast>) => void;
  dismiss: (id: string) => void;
  remove: (id: string) => void;
};

/**
 * Toast context
 */
const ToastContext = React.createContext<ToastContext | null>(null);

/**
 * Toast provider props
 */
interface ToastProviderProps {
  children: React.ReactNode;
}

/**
 * Generate a unique ID for toasts
 */
function generateId() {
  return Math.random().toString(36).substring(2, 9);
}

/**
 * Toast provider component
 */
export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = React.useState<ToasterToast[]>([]);

  const add = React.useCallback((toast: Omit<ToasterToast, "id">) => {
    setToasts((state) => [...state, { ...toast, id: generateId() }]);
  }, []);

  const update = React.useCallback(
    (id: string, toast: Partial<ToasterToast>) => {
      setToasts((state) =>
        state.map((t) => (t.id === id ? { ...t, ...toast } : t)),
      );
    },
    [],
  );

  const dismiss = React.useCallback((id: string) => {
    setToasts((state) =>
      state.map((t) => (t.id === id ? { ...t, open: false } : t)),
    );
  }, []);

  const remove = React.useCallback((id: string) => {
    setToasts((state) => state.filter((t) => t.id !== id));
  }, []);

  const contextValue = React.useMemo(
    () => ({
      toasts,
      add,
      update,
      dismiss,
      remove,
    }),
    [toasts, add, update, dismiss, remove],
  );

  return React.createElement(
    ToastContext.Provider,
    { value: contextValue },
    children,
  );
}

/**
 * Hook to use the toast context
 */
export function useToast() {
  const context = React.useContext(ToastContext);

  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }

  return {
    ...context,
    toast: (props: Omit<ToasterToast, "id">) => {
      context.add(props);
    },
  };
}
