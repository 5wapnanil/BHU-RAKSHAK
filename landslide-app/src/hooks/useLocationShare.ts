import { useState, useCallback } from 'react';
import { Share, Alert, Platform } from 'react-native';
import {
  checkLocationPermission,
  requestLocationPermission,
  getCurrentLocation,
  reverseGeocode,
} from '../services/location';
import { translate, DEFAULT_LANGUAGE, type Language } from '../i18n/translate';

type ShareState = 'idle' | 'getting_location' | 'sharing' | 'success' | 'error';

interface UseLocationShareResult {
  shareState: ShareState;
  error: string | null;
  shareLocation: () => Promise<void>;
}

let currentLanguage: Language = DEFAULT_LANGUAGE;

export function setShareLanguage(language: Language): void {
  currentLanguage = language;
}

function t(key: Parameters<typeof translate>[1], params?: Record<string, string | number>): string {
  return translate(currentLanguage, key, params);
}

export function useLocationShare(): UseLocationShareResult {
  const [shareState, setShareState] = useState<ShareState>('idle');
  const [error, setError] = useState<string | null>(null);

  const shareLocation = useCallback(async () => {
    if (shareState === 'getting_location' || shareState === 'sharing') return;

    setError(null);
    setShareState('getting_location');

    try {
      let permission = await checkLocationPermission();

      if (permission === 'undetermined') {
        permission = await requestLocationPermission();
      }

      if (permission !== 'granted') {
        setShareState('error');
        const msg = t('locationShare.permissionRequiredMsg');
        setError(msg);
        Alert.alert(t('locationShare.permissionRequired'), msg);
        return;
      }

      let location;
      try {
        const result = await getCurrentLocation();
        location = result.coords;
      } catch {
        setShareState('error');
        const msg = t('locationShare.locationErrorMsg');
        setError(msg);
        Alert.alert(t('locationShare.locationError'), msg);
        return;
      }

      setShareState('sharing');

      let address: string | null = null;
      try {
        address = await reverseGeocode(location);
      } catch {
        // Geocoding failure is non-blocking — GPS coords are the source of truth
      }

      const lat = location.latitude.toFixed(6);
      const lon = location.longitude.toFixed(6);

      let message: string;
      if (address) {
        message =
          `📍 ${t('locationShare.myCurrentLocation')}\n\n` +
          `${t('locationShare.locationLabel')}: ${address}\n` +
          `${t('locationShare.coordinatesLabel')}: ${lat}, ${lon}\n\n` +
          `${t('locationShare.mayNeedAssistance')}`;
      } else {
        message =
          `📍 ${t('locationShare.myCurrentLocation')}\n\n` +
          `${t('locationShare.latitudeLabel')}: ${lat}\n` +
          `${t('locationShare.longitudeLabel')}: ${lon}\n\n` +
          `${t('locationShare.useTheseCoordinates')}\n` +
          `${t('locationShare.mayNeedAssistance')}`;
      }

      const result = await Share.share(
        {
          message,
          title: t('locationShare.shareTitle'),
        },
        { dialogTitle: t('locationShare.shareDialogTitle') },
      );

      if (result.action === Share.dismissedAction) {
        // User cancelled — not an error
      }

      setShareState('success');
    } catch {
      setShareState('error');
      const msg = t('locationShare.shareErrorMsg');
      setError(msg);
      Alert.alert(t('locationShare.shareError'), msg);
    }
  }, [shareState]);

  return { shareState, error, shareLocation };
}
