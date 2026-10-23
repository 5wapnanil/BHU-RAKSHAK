export type NortheastState =
  | 'Assam'
  | 'ArunachalPradesh'
  | 'Manipur'
  | 'Meghalaya'
  | 'Mizoram'
  | 'Nagaland'
  | 'Sikkim'
  | 'Tripura';

export interface EmergencyNumbers {
  state: NortheastState;
  emergency: string;
  disaster?: string;
  medical?: string;
  police?: string;
  fire?: string;
}

export const NORTHEAST_EMERGENCY_NUMBERS: Record<NortheastState, EmergencyNumbers> = {
  Assam: {
    state: 'Assam',
    emergency: '112',
    disaster: '1077',
    medical: '108',
    police: '100',
    fire: '101',
  },
  ArunachalPradesh: {
    state: 'ArunachalPradesh',
    emergency: '112',
    disaster: '1077',
    medical: '108',
    police: '100',
    fire: '101',
  },
  Manipur: {
    state: 'Manipur',
    emergency: '112',
    disaster: '1077',
    medical: '108',
    police: '100',
    fire: '101',
  },
  Meghalaya: {
    state: 'Meghalaya',
    emergency: '112',
    disaster: '1077',
    medical: '108',
    police: '100',
    fire: '101',
  },
  Mizoram: {
    state: 'Mizoram',
    emergency: '112',
    disaster: '1077',
    medical: '108',
    police: '100',
    fire: '101',
  },
  Nagaland: {
    state: 'Nagaland',
    emergency: '112',
    disaster: '1077',
    medical: '108',
    police: '100',
    fire: '101',
  },
  Sikkim: {
    state: 'Sikkim',
    emergency: '112',
    disaster: '1077',
    medical: '108',
    police: '100',
    fire: '101',
  },
  Tripura: {
    state: 'Tripura',
    emergency: '112',
    disaster: '1077',
    medical: '108',
    police: '100',
    fire: '101',
  },
};

export const DEFAULT_EMERGENCY_NUMBERS: EmergencyNumbers = {
  state: 'Assam',
  emergency: '112',
};

export function getEmergencyNumbersForState(state: NortheastState | string): EmergencyNumbers {
  if (state in NORTHEAST_EMERGENCY_NUMBERS) {
    return NORTHEAST_EMERGENCY_NUMBERS[state as NortheastState];
  }
  return DEFAULT_EMERGENCY_NUMBERS;
}

export function getEmergencyNumber(state: NortheastState | string): string {
  return getEmergencyNumbersForState(state).emergency;
}

const NORTHEAST_BOUNDS: Record<NortheastState, { minLat: number; maxLat: number; minLng: number; maxLng: number }> = {
  Sikkim: { minLat: 27.0, maxLat: 28.1, minLng: 88.0, maxLng: 89.0 },
  ArunachalPradesh: { minLat: 26.3, maxLat: 29.5, minLng: 91.5, maxLng: 97.3 },
  Nagaland: { minLat: 25.2, maxLat: 27.1, minLng: 93.2, maxLng: 95.2 },
  Manipur: { minLat: 23.8, maxLat: 25.7, minLng: 93.0, maxLng: 94.8 },
  Mizoram: { minLat: 21.9, maxLat: 24.5, minLng: 92.2, maxLng: 93.5 },
  Tripura: { minLat: 22.9, maxLat: 24.6, minLng: 91.1, maxLng: 92.4 },
  Meghalaya: { minLat: 25.0, maxLat: 26.6, minLng: 89.7, maxLng: 92.9 },
  Assam: { minLat: 24.1, maxLat: 28.0, minLng: 89.7, maxLng: 96.0 },
};

export function detectNortheastState(latitude: number, longitude: number): NortheastState | null {
  for (const [state, bounds] of Object.entries(NORTHEAST_BOUNDS)) {
    if (
      latitude >= bounds.minLat &&
      latitude <= bounds.maxLat &&
      longitude >= bounds.minLng &&
      longitude <= bounds.maxLng
    ) {
      return state as NortheastState;
    }
  }
  return null;
}