import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export function useHealthCheck(interval = 30000) {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const check = async () => {
      try {
        setLoading(true);
        const data = await api.get('/api/health/');
        setHealth(data);
        setError(null);
      } catch (error) {
        setHealth(null);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    // Initial check
    check();

    // Set up interval
    const intervalId = setInterval(check, interval);

    // Cleanup
    return () => clearInterval(intervalId);
  }, [interval]);

  return { health, loading, error };
} 