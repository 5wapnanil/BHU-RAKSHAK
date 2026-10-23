import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  DEFAULT_LANGUAGE,
  LANGUAGE_STORAGE_KEY,
  translate,
  type Language,
  type TranslationKey,
} from './translate';
import { setShareLanguage } from '../hooks/useLocationShare';
import { setSOSLanguage } from '../hooks/useSOS';

interface LanguageContextValue {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}

export type { LanguageContextValue };

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>(DEFAULT_LANGUAGE);

  useEffect(() => {
    setShareLanguage(DEFAULT_LANGUAGE);
    setSOSLanguage(DEFAULT_LANGUAGE);
    AsyncStorage.getItem(LANGUAGE_STORAGE_KEY)
      .then((raw) => {
        if (raw === 'en' || raw === 'hi') {
          setLanguageState(raw);
          setShareLanguage(raw);
          setSOSLanguage(raw);
        }
      })
      .catch(() => {
        // Non-blocking — default to English
      });
  }, []);

  const setLanguage = useCallback((next: Language) => {
    setLanguageState(next);
    setShareLanguage(next);
    setSOSLanguage(next);
    AsyncStorage.setItem(LANGUAGE_STORAGE_KEY, next).catch(() => {
      // Non-blocking persistence
    });
  }, []);

  const t = useCallback(
    (key: TranslationKey, params?: Record<string, string | number>) =>
      translate(language, key, params),
    [language],
  );

  const value = useMemo(
    () => ({ language, setLanguage, t }),
    [language, setLanguage, t],
  );

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage(): LanguageContextValue {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
