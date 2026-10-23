import { useState, useCallback } from 'react';
import {
  checkLocationPermission,
  requestLocationPermission,
  getCurrentLocation,
  reverseGeocode,
} from '../services/location';
import type { LocationCoords, LocationPermissionStatus } from '../services/location';

export type LocationState = 'idle' | 'requesting_permission' | 'locating' | 'success' | 'permission_denied' | 'error';

export interface UseCurrentLocationResult {
  location: LocationCoords | null;
  state: LocationState;
  error: string | null;
  permissionStatus: LocationPermissionStatus;
  address: string | null;
  getLocation: () => Promise<void>;
  reset: () => void;
}

export function useCurrentLocation(): UseCurrentLocationResult {
  const [location, setLocation] = useState<LocationCoords | null>(null);
  const [state, setState] = useState<LocationState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [permissionStatus, setPermissionStatus] = useState<LocationPermissionStatus>('undetermined');
  const [address, setAddress] = useState<string | null>(null);

  const getLocation = useCallback(async () => {
    try {
      setState('requesting_permission');
      setError(null);
      setAddress(null);

      const currentPermission = await checkLocationPermission();
      setPermissionStatus(currentPermission);

      let permission = currentPermission;

      if (permission === 'undetermined') {
        permission = await requestLocationPermission();
        setPermissionStatus(permission);
      }

      if (permission !== 'granted') {
        setState('permission_denied');
        setError('Location permission is required to detect your current location.');
        return;
      }

      setState('locating');
      const result = await getCurrentLocation();

      setLocation(result.coords);

      const resolvedAddress = await reverseGeocode(result.coords);
      setAddress(resolvedAddress);

      setState('success');
    } catch (err: unknown) {
      const locationError = err as { code?: string; message?: string };

      if (locationError?.code === 'permission_denied') {
        setState('permission_denied');
        setError('Location permission is required to detect your current location.');
      } else {
        setState('error');
        setError('Unable to detect your location. Please enter it manually.');
      }
    }
  }, []);

  const reset = useCallback(() => {
    setLocation(null);
    setState('idle');
    setError(null);
    setAddress(null);
  }, []);

  return {
    location,
    state,
    error,
    permissionStatus,
    address,
    getLocation,
    reset,
  };
}
