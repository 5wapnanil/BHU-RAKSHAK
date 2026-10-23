import { Platform } from 'react-native';

const elevationValues = {
  none: 0,
  low: 2,
  medium: 4,
  high: 8,
  highest: 16,
} as const;

export const shadows = Platform.select({
  android: {
    none: { elevation: elevationValues.none },
    low: { elevation: elevationValues.low, shadowColor: '#000' },
    medium: { elevation: elevationValues.medium, shadowColor: '#000' },
    high: { elevation: elevationValues.high, shadowColor: '#000' },
    highest: { elevation: elevationValues.highest, shadowColor: '#000' },
  },
  ios: {
    none: {
      shadowColor: 'transparent',
      shadowOffset: { width: 0, height: 0 },
      shadowOpacity: 0,
      shadowRadius: 0,
    },
    low: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.08,
      shadowRadius: 2,
      elevation: elevationValues.low,
    },
    medium: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.12,
      shadowRadius: 4,
      elevation: elevationValues.medium,
    },
    high: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.15,
      shadowRadius: 8,
      elevation: elevationValues.high,
    },
    highest: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.2,
      shadowRadius: 16,
      elevation: elevationValues.highest,
    },
  },
}) as Record<string, object>;

export type ShadowLevel = keyof typeof shadows;
