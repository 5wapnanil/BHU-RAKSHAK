export type SevenSistersState =
  | 'Assam'
  | 'Arunachal Pradesh'
  | 'Manipur'
  | 'Meghalaya'
  | 'Mizoram'
  | 'Nagaland'
  | 'Tripura';

export interface EmergencyContactEntry {
  service: string;
  phones: string[];
  icon: string;
  verified: boolean;
  source: string;
}

export type OneTapKey = 'police' | 'medical' | 'fire' | 'disaster';

export const SEVEN_SISTERS: { key: SevenSistersState; label: string }[] = [
  { key: 'Assam', label: 'ASSAM' },
  { key: 'Arunachal Pradesh', label: 'ARUNACHAL PRADESH' },
  { key: 'Manipur', label: 'MANIPUR' },
  { key: 'Meghalaya', label: 'MEGHALAYA' },
  { key: 'Mizoram', label: 'MIZORAM' },
  { key: 'Nagaland', label: 'NAGALAND' },
  { key: 'Tripura', label: 'TRIPURA' },
];

export const ONE_TAP_SERVICES: {
  key: OneTapKey;
  label: string;
  icon: string;
  bgColor: string;
  iconColor: string;
}[] = [
  { key: 'police', label: 'Police', icon: 'shield-outline', bgColor: '#E3F2FD', iconColor: '#1976D2' },
  { key: 'medical', label: 'Medical', icon: 'medkit-outline', bgColor: '#E8F5E9', iconColor: '#388E3C' },
  { key: 'fire', label: 'Fire & Rescue', icon: 'flame-outline', bgColor: '#FFF3E0', iconColor: '#F57C00' },
  { key: 'disaster', label: 'Disaster Response', icon: 'alert-circle-outline', bgColor: '#FFEBEE', iconColor: '#D32F2F' },
];

export const EMERGENCY_DIRECTORY: Record<SevenSistersState, EmergencyContactEntry[]> = {
  Assam: [
    { service: 'Emergency Response', phones: ['112'], icon: 'call-outline', verified: true, source: 'Government of Assam' },
    { service: 'Police', phones: ['100'], icon: 'shield-outline', verified: true, source: 'Assam Police' },
    { service: 'Medical', phones: ['108'], icon: 'medkit-outline', verified: true, source: 'National Health Authority' },
    { service: 'Disaster Management', phones: ['1070', '1077'], icon: 'alert-circle-outline', verified: true, source: 'ASDMA' },
    { service: 'Child Helpline', phones: ['1098'], icon: 'people-outline', verified: true, source: 'Childline India' },
    { service: 'Women Helpline', phones: ['181'], icon: 'woman-outline', verified: true, source: 'Women Helpline India' },
    { service: 'ASDMA State Office', phones: ['0361-2237221'], icon: 'business-outline', verified: true, source: 'ASDMA' },
  ],
  'Arunachal Pradesh': [
    { service: 'Emergency Response', phones: ['112'], icon: 'call-outline', verified: true, source: 'Government of Arunachal Pradesh' },
    { service: 'Police', phones: ['100', '0360-221-1000'], icon: 'shield-outline', verified: true, source: 'Arunachal Pradesh Police' },
    { service: 'Medical', phones: ['108', '0360-221-1080'], icon: 'medkit-outline', verified: true, source: 'State Health Department' },
    { service: 'Fire & Rescue', phones: ['101', '0360-221-1010'], icon: 'flame-outline', verified: true, source: 'AP Fire Services' },
  ],
  Manipur: [
    { service: 'Emergency Response', phones: ['112'], icon: 'call-outline', verified: true, source: 'Government of Manipur' },
  ],
  Meghalaya: [
    { service: 'Emergency Response', phones: ['112'], icon: 'call-outline', verified: true, source: 'Government of Meghalaya' },
    { service: 'Police', phones: ['100'], icon: 'shield-outline', verified: true, source: 'Meghalaya Police' },
    { service: 'Fire', phones: ['101'], icon: 'flame-outline', verified: true, source: 'Meghalaya Fire Services' },
    { service: 'Medical', phones: ['108'], icon: 'medkit-outline', verified: true, source: 'National Health Authority' },
    { service: 'Women Helpline', phones: ['1091', '181'], icon: 'woman-outline', verified: true, source: 'Women Helpline India' },
    { service: 'Child Helpline', phones: ['1098'], icon: 'people-outline', verified: true, source: 'Childline India' },
    { service: 'Electricity', phones: ['1912'], icon: 'flash-outline', verified: true, source: 'Meghalaya Electricity' },
  ],
  Mizoram: [
    { service: 'Emergency Response', phones: ['112'], icon: 'call-outline', verified: true, source: 'Government of Mizoram' },
    { service: 'State Emergency Operation Centre', phones: ['1070'], icon: 'alert-circle-outline', verified: true, source: 'Mizoram SDMA' },
    { service: 'SEOC Direct', phones: ['0389-2342520'], icon: 'call-outline', verified: true, source: 'Mizoram SDMA' },
    { service: 'District Emergency Operation Centre', phones: ['1077'], icon: 'alert-circle-outline', verified: true, source: 'Mizoram SDMA' },
  ],
  Nagaland: [
    { service: 'Emergency Response', phones: ['112'], icon: 'call-outline', verified: true, source: 'Government of Nagaland' },
    { service: 'State Emergency Operation Centre', phones: ['1070'], icon: 'alert-circle-outline', verified: true, source: 'Nagaland SDMA' },
    { service: 'SEOC Direct', phones: ['0370-2291120', '0370-2291122'], icon: 'call-outline', verified: true, source: 'Nagaland SDMA' },
  ],
  Tripura: [
    { service: 'Emergency Response', phones: ['112'], icon: 'call-outline', verified: true, source: 'Government of Tripura' },
    { service: 'State Emergency Operation Centre', phones: ['1070'], icon: 'alert-circle-outline', verified: true, source: 'Tripura SDMA' },
    { service: 'District Emergency Operation Centre', phones: ['1077'], icon: 'alert-circle-outline', verified: true, source: 'Tripura SDMA' },
    { service: 'State EOC Direct', phones: ['0381-2416045', '0381-2416241'], icon: 'call-outline', verified: true, source: 'Tripura SDMA' },
  ],
};

const SERVICE_KEY_MAP: Record<OneTapKey, string[]> = {
  police: ['Police'],
  medical: ['Medical'],
  fire: ['Fire', 'Fire & Rescue'],
  disaster: ['Disaster Management', 'State Emergency Operation Centre', 'District Emergency Operation Centre', 'SEOC Direct', 'State EOC Direct'],
};

export function getOneTapNumber(state: SevenSistersState, key: OneTapKey): string {
  const contacts = EMERGENCY_DIRECTORY[state];
  const serviceNames = SERVICE_KEY_MAP[key];
  for (const contact of contacts) {
    if (serviceNames.includes(contact.service) && contact.phones.length > 0) {
      return contact.phones[0];
    }
  }
  return '112';
}

export interface SituationInfo {
  key: string;
  label: string;
  emoji: string;
  serviceKey: OneTapKey | 'women' | 'child' | 'electricity' | null;
  fallback: string;
}

export const SITUATIONS: SituationInfo[] = [
  { key: 'landslide', label: 'Landslide', emoji: '🏔️', serviceKey: 'disaster', fallback: '112' },
  { key: 'flood', label: 'Flood', emoji: '🌊', serviceKey: 'disaster', fallback: '112' },
  { key: 'fire', label: 'Fire', emoji: '🔥', serviceKey: 'fire', fallback: '112' },
  { key: 'medical', label: 'Medical Emergency', emoji: '🚑', serviceKey: 'medical', fallback: '112' },
  { key: 'crime', label: 'Crime / Security', emoji: '👮', serviceKey: 'police', fallback: '112' },
  { key: 'women', label: "Women's Safety", emoji: '👩', serviceKey: 'women', fallback: '112' },
  { key: 'child', label: 'Child Emergency', emoji: '👶', serviceKey: 'child', fallback: '112' },
  { key: 'road', label: 'Road Blockage', emoji: '🚗', serviceKey: 'disaster', fallback: '112' },
  { key: 'building', label: 'Building Collapse', emoji: '🏚️', serviceKey: 'disaster', fallback: '112' },
  { key: 'electrical', label: 'Electrical Hazard', emoji: '⚡', serviceKey: 'electricity', fallback: '112' },
  { key: 'lifethreat', label: 'Life-threatening Emergency', emoji: '🆘', serviceKey: null, fallback: '112' },
];

const SITUATION_SERVICE_MAP: Record<string, string[]> = {
  police: ['Police'],
  medical: ['Medical'],
  fire: ['Fire', 'Fire & Rescue'],
  disaster: ['Disaster Management', 'State Emergency Operation Centre', 'District Emergency Operation Centre', 'SEOC Direct', 'State EOC Direct'],
  women: ['Women Helpline'],
  child: ['Child Helpline'],
  electricity: ['Electricity'],
};

export function getSituationContact(
  state: SevenSistersState,
  situation: SituationInfo
): { service: string; phone: string } {
  if (!situation.serviceKey) {
    return { service: 'Emergency Response', phone: situation.fallback };
  }

  const contacts = EMERGENCY_DIRECTORY[state];
  const serviceNames = SITUATION_SERVICE_MAP[situation.serviceKey] || [];

  for (const contact of contacts) {
    if (serviceNames.includes(contact.service) && contact.phones.length > 0) {
      return { service: contact.service, phone: contact.phones[0] };
    }
  }

  return { service: 'Emergency Response', phone: situation.fallback };
}

export interface EmergencyCircleContact {
  id: string;
  name: string;
  relationship: string;
  phone: string;
}

export const RELATIONSHIP_OPTIONS = ['Family', 'Friend', 'Doctor', 'Local Volunteer', 'Caregiver'];
