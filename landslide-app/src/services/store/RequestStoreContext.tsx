import React, {
  createContext,
  useContext,
  useReducer,
  useEffect,
  useState,
  useRef,
  useCallback,
  ReactNode,
} from 'react';
import type {
  LocalRequest,
  LocalRequestAction,
  LocalRequestState,
  SyncStatus,
} from '../../types';
import { loadRequests, saveRequests } from '../../storage';
import { processSyncQueue } from '../sync';
import { subscribeToNetworkChanges } from '../connectivity/connectivityService';

// ── Reducer ──

const initialState: LocalRequestState = {
  requests: [],
  volunteers: [],
};

function reducer(state: LocalRequestState, action: LocalRequestAction): LocalRequestState {
  switch (action.type) {
    case 'SET_INITIAL_STATE': {
      // If requests or volunteers were added before hydration settled, merge them
      if (state.requests.length === 0 && state.volunteers.length === 0) {
        return action.payload;
      }
      const existingIds = new Set(action.payload.requests.map((r) => r.id));
      const preHydrationRequests = state.requests.filter((r) => !existingIds.has(r.id));
      const existingVolunteerIds = new Set(action.payload.volunteers.map((v) => v.id));
      const preHydrationVolunteers = state.volunteers.filter((v) => !existingVolunteerIds.has(v.id));

      return {
        requests: [...action.payload.requests, ...preHydrationRequests],
        volunteers: [...action.payload.volunteers, ...preHydrationVolunteers],
      };
    }
    case 'ADD_REQUEST': {
      const req = action.payload;
      if (req.type === 'evacuation_volunteer' || req.type === 'relief_volunteer') {
        return {
          ...state,
          requests: [...state.requests, req],
          volunteers: [...state.volunteers, req],
        };
      }
      return {
        ...state,
        requests: [...state.requests, req],
      };
    }
    case 'UPDATE_STATUS': {
      const { id, status } = action.payload;
      const mapUpdate = (item: LocalRequest): LocalRequest =>
        item.id === id ? { ...item, status, updatedAt: new Date().toISOString() } : item;
      return {
        requests: state.requests.map(mapUpdate),
        volunteers: state.volunteers.map(mapUpdate) as LocalRequestState['volunteers'],
      };
    }
    case 'UPDATE_SYNC_STATUS': {
      const { id, syncStatus } = action.payload;
      const mapSync = (item: LocalRequest): LocalRequest =>
        item.id === id ? { ...item, syncStatus, updatedAt: new Date().toISOString() } : item;
      return {
        requests: state.requests.map(mapSync),
        volunteers: state.volunteers.map(mapSync) as LocalRequestState['volunteers'],
      };
    }
    case 'DELETE_REQUEST': {
      const { id } = action.payload;
      return {
        requests: state.requests.filter((r) => r.id !== id),
        volunteers: state.volunteers.filter((v) => v.id !== id),
      };
    }
    default:
      return state;
  }
}

// ── Context ──

interface RequestStoreContextValue {
  state: LocalRequestState;
  dispatch: React.Dispatch<LocalRequestAction>;
  isLoaded: boolean;
}

const RequestStoreContext = createContext<RequestStoreContextValue | undefined>(undefined);

export function RequestStoreProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [isLoaded, setIsLoaded] = useState(false);
  const isHydratedRef = useRef(false);
  const isFirstHydratedEffect = useRef(true);
  const hadPreHydrationChangesRef = useRef(false);
  const isMountedRef = useRef(true);
  const stateRef = useRef(state);
  stateRef.current = state;

  const wrappedDispatch = useCallback((action: LocalRequestAction) => {
    if (!isHydratedRef.current && action.type !== 'SET_INITIAL_STATE') {
      hadPreHydrationChangesRef.current = true;
    }
    dispatch(action);
  }, []);

  // Track mount lifecycle
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Load persisted state on mount
  useEffect(() => {
    async function loadPersistedState() {
      try {
        const loadedState = await loadRequests();
        if (!isMountedRef.current) return;

        // Install persisted state into the reducer
        dispatch({ type: 'SET_INITIAL_STATE', payload: loadedState });
        isHydratedRef.current = true;
        setIsLoaded(true);
      } catch (error) {
        if (!isMountedRef.current) return;
        console.warn('[RequestStoreProvider] Failed to load persisted state:', error);
        // Hydration failure: leave isLoaded and isHydratedRef false.
        // Never overwrite potentially recoverable storage with initialState!
      }
    }

    loadPersistedState();
  }, []);

  // Persist state whenever it changes AFTER hydration has completed
  useEffect(() => {
    if (!isHydratedRef.current || !isLoaded) {
      return;
    }

    // On the initial hydration render, the state in memory matches the loaded state in storage.
    // Only write to storage if pre-hydration requests were merged in.
    if (isFirstHydratedEffect.current) {
      isFirstHydratedEffect.current = false;
      if (hadPreHydrationChangesRef.current) {
        saveRequests(state);
      }
      return;
    }

    saveRequests(state);
  }, [state, isLoaded]);

  // ── Sync queue recovery ──

  const findRequest = (id: string): LocalRequest | undefined => {
    return stateRef.current.requests.find((r) => r.id === id);
  };

  const updateSyncStatus = (id: string, syncStatus: SyncStatus) => {
    wrappedDispatch({ type: 'UPDATE_SYNC_STATUS', payload: { id, syncStatus } });
  };

  // Startup recovery: process queue after state is loaded and hydrated
  useEffect(() => {
    if (!isLoaded || !isHydratedRef.current) return;

    const timer = setTimeout(() => {
      processSyncQueue(findRequest, updateSyncStatus);
    }, 3000);

    return () => clearTimeout(timer);
  }, [isLoaded]);

  // Connectivity recovery: process queue when network comes back and store is hydrated
  useEffect(() => {
    const unsubscribe = subscribeToNetworkChanges((isConnected) => {
      if (isConnected && isLoaded && isHydratedRef.current) {
        setTimeout(() => {
          processSyncQueue(findRequest, updateSyncStatus);
        }, 2000);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [isLoaded]);

  return (
    <RequestStoreContext.Provider value={{ state, dispatch: wrappedDispatch, isLoaded }}>
      {children}
    </RequestStoreContext.Provider>
  );
}

export function useRequestStore(): RequestStoreContextValue {
  const ctx = useContext(RequestStoreContext);
  if (!ctx) {
    throw new Error('useRequestStore must be used within a RequestStoreProvider');
  }
  return ctx;
}
