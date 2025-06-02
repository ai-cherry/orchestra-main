import { act, renderHook } from '@testing-library/react';
import usePersonaStore, { 
  Persona, 
  PersonaSettings,
  useActivePersona,
  usePersonaById,
  useAllPersonas,
  usePersonaActions
} from '../personaStore';

describe('PersonaStore', () => {
  // Helper to get fresh store state
  const getStore = () => usePersonaStore.getState();

  beforeEach(() => {
    // Reset store to initial state before each test
    act(() => {
      getStore().reset();
    });
  });

  describe('Initial State', () => {
    it('should have initial personas', () => {
      const { personas } = getStore();
      expect(personas).toHaveLength(3);
      expect(personas.map(p => p.id)).toEqual(['cherry', 'sophia', 'karen']);
    });

    it('should have cherry as default active persona', () => {
      const { activePersonaId } = getStore();
      expect(activePersonaId).toBe('cherry');
    });

    it('should not be loading initially', () => {
      const { isLoading, error } = getStore();
      expect(isLoading).toBe(false);
      expect(error).toBeNull();
    });
  });

  describe('Active Persona Management', () => {
    it('should set active persona', () => {
      act(() => {
        getStore().setActivePersona('sophia');
      });

      expect(getStore().activePersonaId).toBe('sophia');
      expect(getStore().getActivePersona()?.id).toBe('sophia');
    });

    it('should not set invalid persona as active', () => {
      const initialId = getStore().activePersonaId;
      
      act(() => {
        getStore().setActivePersona('invalid-id');
      });

      expect(getStore().activePersonaId).toBe(initialId);
    });

    it('should return active persona correctly', () => {
      const activePersona = getStore().getActivePersona();
      expect(activePersona?.id).toBe('cherry');
      expect(activePersona?.name).toBe('Cherry');
    });
  });

  describe('CRUD Operations', () => {
    it('should add a new persona', () => {
      const newPersona: Persona = {
        id: 'test-persona',
        name: 'Test Assistant',
        domain: 'Testing',
        role: 'QA Assistant',
        description: 'Test description',
        color: '#123456',
        permissions: ['test'],
      };

      act(() => {
        getStore().addPersona(newPersona);
      });

      const personas = getStore().personas;
      expect(personas).toHaveLength(4);
      expect(personas.find(p => p.id === 'test-persona')).toBeDefined();
    });

    it('should update an existing persona', () => {
      act(() => {
        getStore().updatePersona('cherry', {
          name: 'Cherry Updated',
          description: 'Updated description',
        });
      });

      const updatedPersona = getStore().getPersonaById('cherry');
      expect(updatedPersona?.name).toBe('Cherry Updated');
      expect(updatedPersona?.description).toBe('Updated description');
      expect(updatedPersona?.domain).toBe('Personal'); // Unchanged
    });

    it('should remove a persona', () => {
      act(() => {
        getStore().removePersona('karen');
      });

      const personas = getStore().personas;
      expect(personas).toHaveLength(2);
      expect(personas.find(p => p.id === 'karen')).toBeUndefined();
    });

    it('should update active persona when removing current active', () => {
      act(() => {
        getStore().setActivePersona('karen');
        getStore().removePersona('karen');
      });

      expect(getStore().activePersonaId).toBe('cherry'); // Falls back to first
    });
  });

  describe('Batch Operations', () => {
    it('should add multiple personas at once', () => {
      const newPersonas: Persona[] = [
        {
          id: 'test1',
          name: 'Test 1',
          domain: 'Domain 1',
          role: 'Role 1',
          description: 'Desc 1',
          color: '#111111',
        },
        {
          id: 'test2',
          name: 'Test 2',
          domain: 'Domain 2',
          role: 'Role 2',
          description: 'Desc 2',
          color: '#222222',
        },
      ];

      act(() => {
        getStore().addMultiplePersonas(newPersonas);
      });

      expect(getStore().personas).toHaveLength(5);
    });

    it('should update multiple personas at once', () => {
      const updates = [
        { id: 'cherry', updates: { name: 'Cherry Modified' } },
        { id: 'sophia', updates: { name: 'Sophia Modified' } },
      ];

      act(() => {
        getStore().updateMultiplePersonas(updates);
      });

      expect(getStore().getPersonaById('cherry')?.name).toBe('Cherry Modified');
      expect(getStore().getPersonaById('sophia')?.name).toBe('Sophia Modified');
    });

    it('should remove multiple personas at once', () => {
      act(() => {
        getStore().removeMultiplePersonas(['cherry', 'sophia']);
      });

      expect(getStore().personas).toHaveLength(1);
      expect(getStore().personas[0].id).toBe('karen');
    });
  });

  describe('Settings Management', () => {
    it('should update persona settings', () => {
      const newSettings: Partial<PersonaSettings> = {
        theme: {
          primaryColor: '#FF0000',
          secondaryColor: '#00FF00',
        },
        features: {
          darkMode: true,
          analytics: false,
        },
      };

      act(() => {
        getStore().updatePersonaSettings('cherry', newSettings);
      });

      const persona = getStore().getPersonaById('cherry');
      expect(persona?.settings?.theme?.primaryColor).toBe('#FF0000');
      expect(persona?.settings?.features?.darkMode).toBe(true);
    });
  });

  describe('Loading and Error States', () => {
    it('should set loading state', () => {
      act(() => {
        getStore().setLoading(true);
      });

      expect(getStore().isLoading).toBe(true);
    });

    it('should set error state', () => {
      act(() => {
        getStore().setError('Test error message');
      });

      expect(getStore().error).toBe('Test error message');
    });

    it('should clear error state', () => {
      act(() => {
        getStore().setError('Test error');
        getStore().clearError();
      });

      expect(getStore().error).toBeNull();
    });
  });

  describe('Sync Status', () => {
    it('should update sync status', () => {
      act(() => {
        getStore().setSyncStatus({
          isSyncing: true,
          error: 'Sync failed',
        });
      });

      const { syncStatus } = getStore();
      expect(syncStatus.isSyncing).toBe(true);
      expect(syncStatus.error).toBe('Sync failed');
    });

    it('should mark as synced', () => {
      act(() => {
        getStore().markAsSynced();
      });

      const { syncStatus } = getStore();
      expect(syncStatus.isSyncing).toBe(false);
      expect(syncStatus.lastSyncedAt).toBeDefined();
      expect(syncStatus.error).toBeUndefined();
    });
  });

  describe('Hooks', () => {
    it('useActivePersona should return active persona', () => {
      const { result } = renderHook(() => useActivePersona());
      expect(result.current?.id).toBe('cherry');
    });

    it('usePersonaById should return specific persona', () => {
      const { result } = renderHook(() => usePersonaById('sophia'));
      expect(result.current?.name).toBe('Sophia');
    });

    it('useAllPersonas should return all personas', () => {
      const { result } = renderHook(() => useAllPersonas());
      expect(result.current).toHaveLength(3);
    });

    it('usePersonaActions should return action functions', () => {
      const { result } = renderHook(() => usePersonaActions());
      
      expect(typeof result.current.setActivePersona).toBe('function');
      expect(typeof result.current.addPersona).toBe('function');
      expect(typeof result.current.updatePersona).toBe('function');
      expect(typeof result.current.removePersona).toBe('function');
      expect(typeof result.current.updatePersonaSettings).toBe('function');
    });
  });

  describe('Persistence', () => {
    it('should persist active persona ID', () => {
      act(() => {
        getStore().setActivePersona('sophia');
      });

      // Simulate store rehydration
      const persistedState = localStorage.getItem('persona-storage');
      expect(persistedState).toBeTruthy();
      
      const parsed = JSON.parse(persistedState!);
      expect(parsed.state.activePersonaId).toBe('sophia');
    });

    it('should persist custom personas', () => {
      const customPersona: Persona = {
        id: 'custom',
        name: 'Custom',
        domain: 'Custom Domain',
        role: 'Custom Role',
        description: 'Custom description',
        color: '#CUSTOM',
      };

      act(() => {
        getStore().addPersona(customPersona);
      });

      const persistedState = localStorage.getItem('persona-storage');
      const parsed = JSON.parse(persistedState!);
      
      expect(parsed.state.personas).toContainEqual(
        expect.objectContaining({ id: 'custom' })
      );
    });
  });

  describe('Computed Properties', () => {
    it('should compute activePersona getter correctly', () => {
      const store = getStore();
      expect(store.activePersona?.id).toBe('cherry');

      act(() => {
        store.setActivePersona('sophia');
      });

      expect(getStore().activePersona?.id).toBe('sophia');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty personas array', () => {
      act(() => {
        getStore().setPersonas([]);
      });

      expect(getStore().personas).toHaveLength(0);
      expect(getStore().getActivePersona()).toBeNull();
    });

    it('should handle updating non-existent persona', () => {
      const personasBefore = getStore().personas.length;
      
      act(() => {
        getStore().updatePersona('non-existent', { name: 'Test' });
      });

      expect(getStore().personas.length).toBe(personasBefore);
    });

    it('should add timestamps to new personas', () => {
      const newPersona: Persona = {
        id: 'timestamped',
        name: 'Timestamped',
        domain: 'Test',
        role: 'Test',
        description: 'Test',
        color: '#000000',
      };

      act(() => {
        getStore().addPersona(newPersona);
      });

      const added = getStore().getPersonaById('timestamped');
      expect(added?.createdAt).toBeDefined();
      expect(added?.updatedAt).toBeDefined();
    });
  });
});