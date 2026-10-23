import { useCallback, useState } from 'react';
import { Alert, Linking } from 'react-native';
import {
  checkLocationPermission,
  requestLocationPermission,
  getCurrentLocation,
} from '../services/location';
import { translate, DEFAULT_LANGUAGE, type Language, type TranslationKey } from '../i18n/translate';

export type SOSState = 'idle' | 'opening_dialer' | 'error';

export interface UseSOSResult {
  state: SOSState;
  error: string | null;
  activateSOS: () => Promise<boolean>;
  reset: () => void;
}

const UNIVERSAL_EMERGENCY = '112';

let currentLanguage: Language = DEFAULT_LANGUAGE;

export function setSOSLanguage(language: Language): void {
  currentLanguage = language;
}

function t(key: TranslationKey, params?: Record<string, string | number>): string {
  return translate(currentLanguage, key, params);
}

export function useSOS(): UseSOSResult {
  const [state, setState] = useState<SOSState>('idle');
  const [error, setError] = useState<string | null>(null);

  const activateSOS = useCallback(async (): Promise<boolean> => {
    setError(null);

    // GPS is obtained independently — must not delay the dialer
    (async () => {
      try {
        let permission = await checkLocationPermission();
        if (permission === 'undetermined') {
          permission = await requestLocationPermission();
        }
        if (permission === 'granted') {
          await getCurrentLocation();
        }
      } catch {
        // GPS failed — non-critical, dialer must not depend on GPS
      }
    })();

    // 112 is universal — open the dialer immediately
    try {
      setState('opening_dialer');
      await Linking.openURL(`tel:${UNIVERSAL_EMERGENCY}`);
      setState('idle');
      return true;
    } catch {
      setState('error');
      const message = t('sos.dialerFailed');
      setError(message);
      Alert.alert(
        t('sos.errorTitle'),
        message,
        [
          {
            text: t('common.ok'),
            onPress: () => {
              setState('idle');
            },
          },
        ],
        {
          cancelable: true,
          onDismiss: () => {
            setState('idle');
          },
        }
      );
      return false;
    }
  }, []);

  const reset = useCallback(() => {
    setState('idle');
    setError(null);
  }, []);

  return {
    state,
    error,
    activateSOS,
    reset,
  };
}
