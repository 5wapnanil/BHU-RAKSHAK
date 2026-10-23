export const colors = {
  primary: '#E8654A',
  primaryLight: '#F4937E',
  primaryDark: '#C94A32',

  secondary: '#2D2D2D',

  background: '#FFFFFF',
  backgroundLight: '#F8F8F8',
  backgroundGray: '#F0F0F0',

  surface: '#FFFFFF',
  surfaceGray: '#F5F5F5',

  text: '#1A1A1A',
  textSecondary: '#666666',
  textLight: '#999999',
  textWhite: '#FFFFFF',

  border: '#E0E0E0',
  borderLight: '#F0F0F0',

  error: '#D32F2F',
  errorLight: '#FFEBEE',
  success: '#4CAF50',
  successLight: '#E8F5E9',
  warning: '#FF9800',
  warningLight: '#FFF3E0',
  info: '#2196F3',
  infoLight: '#E3F2FD',

  sosBackground: '#FDE8E4',
  sosRing: '#F4937E',
  sosRingOuter: '#FADBD8',
  sosButton: '#E8654A',

  overlay: 'rgba(0,0,0,0.5)',
  shadow: '#000000',

  white: '#FFFFFF',
  black: '#000000',
} as const;

export type ColorKey = keyof typeof colors;
