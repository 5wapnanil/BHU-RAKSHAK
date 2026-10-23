import { en, type Translations } from './translations/en';
import { hi } from './translations/hi';

export type Language = 'en' | 'hi';

export const DEFAULT_LANGUAGE: Language = 'en';

export const LANGUAGES: { key: Language; label: string }[] = [
  { key: 'en', label: 'English' },
  { key: 'hi', label: 'हिन्दी' },
];

export const TRANSLATIONS: Record<Language, Translations> = {
  en,
  hi,
};

export const LANGUAGE_STORAGE_KEY = '@aidconnect_language';

type NestedKeyOf<T> = T extends string
  ? never
  : T extends readonly (infer U)[]
    ? `${number}` | (U extends string ? never : `${number}.${NestedKeyOf<U>}`)
    : {
        [K in keyof T & string]: T[K] extends string ? K : `${K}.${NestedKeyOf<T[K]>}`;
      }[keyof T & string];

export type TranslationKey = NestedKeyOf<Translations>;

export function translate(
  language: Language,
  key: TranslationKey,
  params?: Record<string, string | number>,
): string {
  const dict = TRANSLATIONS[language] as unknown;
  const enDict = TRANSLATIONS[DEFAULT_LANGUAGE] as unknown;

  const segments = key.split('.');
  let current: unknown = dict;
  let fallback: unknown = enDict;

  for (const segment of segments) {
    if (
      current !== null &&
      current !== undefined &&
      typeof current === 'object' &&
      segment in (current as Record<string, unknown>)
    ) {
      current = (current as Record<string, unknown>)[segment];
    } else {
      current = undefined;
      break;
    }

    if (
      fallback !== null &&
      fallback !== undefined &&
      typeof fallback === 'object' &&
      segment in (fallback as Record<string, unknown>)
    ) {
      fallback = (fallback as Record<string, unknown>)[segment];
    } else {
      fallback = undefined;
      break;
    }
  }

  let result: unknown;
  if (typeof current === 'string') {
    result = current;
  } else if (typeof fallback === 'string') {
    if (__DEV__ && language !== DEFAULT_LANGUAGE) {
      console.warn(`[i18n] Missing key "${key}" for language "${language}" — using English fallback.`);
    }
    result = fallback;
  } else {
    if (__DEV__) {
      console.warn(`[i18n] Missing key "${key}" for all languages.`);
    }
    result = key;
  }

  if (params && typeof result === 'string') {
    return result.replace(/\{(\w+)\}/g, (match, name: string) =>
      name in params ? String(params[name]) : match,
    );
  }

  return String(result);
}

export type { Translations };
