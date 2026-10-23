import * as Location from 'expo-location';

export type LocationPermissionStatus = 'undetermined' | 'granted' | 'denied' | 'unavailable';

export interface LocationCoords {
  latitude: number;
  longitude: number;
}

export interface LocationResult {
  coords: LocationCoords;
  timestamp: number;
}

export interface LocationError {
  code: LocationErrorCode;
  message: string;
}

export type LocationErrorCode =
  | 'permission_denied'
  | 'permission_unavailable'
  | 'location_unavailable'
  | 'timeout'
  | 'unknown';

export async function checkLocationPermission(): Promise<LocationPermissionStatus> {
  try {
    const { status } = await Location.getForegroundPermissionsAsync();
    
    switch (status) {
      case Location.PermissionStatus.GRANTED:
        return 'granted';
      case Location.PermissionStatus.DENIED:
        return 'denied';
      case Location.PermissionStatus.UNDETERMINED:
        return 'undetermined';
      default:
        return 'unavailable';
    }
  } catch (error) {
    console.warn('[LocationService] Failed to check permission:', error);
    return 'unavailable';
  }
}

export async function requestLocationPermission(): Promise<LocationPermissionStatus> {
  try {
    const { status } = await Location.requestForegroundPermissionsAsync();
    
    switch (status) {
      case Location.PermissionStatus.GRANTED:
        return 'granted';
      case Location.PermissionStatus.DENIED:
        return 'denied';
      case Location.PermissionStatus.UNDETERMINED:
        return 'undetermined';
      default:
        return 'unavailable';
    }
  } catch (error) {
    console.warn('[LocationService] Failed to request permission:', error);
    return 'unavailable';
  }
}

export async function getCurrentLocation(): Promise<LocationResult> {
  const permission = await checkLocationPermission();
  
  if (permission !== 'granted') {
    throw {
      code: permission === 'denied' ? 'permission_denied' : 'permission_unavailable',
      message: 'Location permission is not granted',
    } as LocationError;
  }

  try {
    const location = await Location.getCurrentPositionAsync({
      accuracy: Location.Accuracy.Balanced,
    });

    return {
      coords: {
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
      },
      timestamp: location.timestamp,
    };
  } catch (error: unknown) {
    const locationError = error as { code?: string; message?: string };
    
    if (locationError?.code === 'E_LOCATION_TIMEOUT') {
      throw {
        code: 'timeout',
        message: 'Location request timed out',
      } as LocationError;
    }
    
    if (locationError?.code === 'E_LOCATION_UNAVAILABLE') {
      throw {
        code: 'location_unavailable',
        message: 'Location is currently unavailable',
      } as LocationError;
    }

    throw {
      code: 'unknown',
      message: 'Failed to get current location',
    } as LocationError;
  }
}

const GEOCODE_TIMEOUT_MS = 5000;

export async function reverseGeocode(coords: LocationCoords): Promise<string | null> {
  // Try Expo geocoder with a short timeout; fall through to Nominatim if it's slow or fails
  try {
    const results = await Promise.race([
      Location.reverseGeocodeAsync({
        latitude: coords.latitude,
        longitude: coords.longitude,
      }),
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('Expo geocoder timeout')), GEOCODE_TIMEOUT_MS),
      ),
    ]);

    if (results.length > 0) {
      const result = results[0];
      const parts: string[] = [];

      if (result.city) {
        parts.push(result.city);
      } else if (result.district) {
        parts.push(result.district);
      } else if (result.subregion) {
        parts.push(result.subregion);
      }

      if (result.region) {
        parts.push(result.region);
      }

      if (result.country) {
        parts.push(result.country);
      }

      const address = parts.filter(Boolean).join(', ');
      if (address.length > 0) return address;
    }
  } catch {
    // Expo geocoder unavailable or timed out — continue to Nominatim
  }

  // Fallback: OpenStreetMap Nominatim
  try {
    const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${coords.latitude}&lon=${coords.longitude}`;
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) return null;

    const data = await response.json();
    const addr = data?.address;

    if (!addr) return null;

    const parts: string[] = [];

    if (addr.city || addr.town || addr.village) {
      parts.push(addr.city || addr.town || addr.village);
    } else if (addr.county) {
      parts.push(addr.county);
    }

    if (addr.state) {
      parts.push(addr.state);
    }

    if (addr.country) {
      parts.push(addr.country);
    }

    const address = parts.filter(Boolean).join(', ');
    return address.length > 0 ? address : null;
  } catch (error) {
    console.warn('[LocationService] Nominatim fallback failed:', error);
    return null;
  }
}