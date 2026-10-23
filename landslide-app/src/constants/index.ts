import { EmergencyType } from '../types';
import {
  NORTHEAST_EMERGENCY_NUMBERS,
  DEFAULT_EMERGENCY_NUMBERS,
  getEmergencyNumbersForState,
  getEmergencyNumber,
  detectNortheastState,
  type NortheastState,
  type EmergencyNumbers,
} from './emergencyNumbers';

export const APP_NAME = 'AidConnect';

export const API_CONFIG = {
  baseUrl: '',
  timeout: 30000,
};

export const EMERGENCY_TYPES: { key: EmergencyType; label: string; icon: string }[] = [
  { key: 'fire', label: 'Fire', icon: 'flame-outline' },
  { key: 'earthquake', label: 'Earthquake', icon: 'pulse-outline' },
  { key: 'flood', label: 'Flood', icon: 'water-outline' },
  { key: 'landslide', label: 'Landslide', icon: 'mountain-outline' },
  { key: 'cyclone', label: 'Cyclone', icon: 'thunderstorm-outline' },
  { key: 'other', label: 'Other', icon: 'ellipsis-horizontal-outline' },
];

export const QUICK_ACTIONS = [
  { key: 'assistance', label: 'I need assistance', icon: 'hand-left-outline' },
  { key: 'routes', label: 'Show me safe routes', icon: 'navigate-outline' },
  { key: 'testing', label: 'Testing notifications', icon: 'notifications-outline' },
];

export const SHELTER_TABS = [
  { key: 'hospitals', label: 'Hospitals', icon: 'medkit-outline' },
  { key: 'rescueCamps', label: 'Rescue Camps', icon: 'campground-outline' },
  { key: 'policeStations', label: 'Police Stations', icon: 'shield-outline' },
  { key: 'fireStations', label: 'Fire Stations', icon: 'flame-outline' },
  { key: 'reliefCenters', label: 'Relief Centers', icon: 'heart-outline' },
];

export const SAFETY_TIPS = [
  {
    id: '1',
    title: 'Disaster Preparedness',
    description: 'Be Prepared: Build an emergency kit and make a family evacuation plan.',
    category: 'preparedness',
  },
  {
    id: '2',
    title: 'First Aid Tips',
    description: 'Learn basic first aid skills to help yourself and others during emergencies.',
    category: 'firstaid',
  },
  {
    id: '3',
    title: 'Help and Rescue Centre',
    description: 'Know your local emergency numbers and nearby rescue centres.',
    category: 'rescue',
  },
  {
    id: '4',
    title: 'Help Others Too',
    description: 'Neighbors helping neighbors during emergencies can save lives.',
    category: 'community',
  },
];

export {
  NORTHEAST_EMERGENCY_NUMBERS,
  DEFAULT_EMERGENCY_NUMBERS,
  getEmergencyNumbersForState,
  getEmergencyNumber,
  detectNortheastState,
  type NortheastState,
  type EmergencyNumbers,
};
