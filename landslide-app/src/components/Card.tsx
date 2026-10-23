import React from 'react';
import { View, Text, StyleSheet, ViewStyle, TouchableOpacity } from 'react-native';
import { colors } from '../theme/colors';
import { borderRadius, spacing, typography } from '../theme';
import { shadows } from '../theme/shadows';
import { useLanguage } from '../i18n';

interface CardProps {
  children?: React.ReactNode;
  style?: ViewStyle;
  onPress?: () => void;
  variant?: 'default' | 'elevated' | 'outlined';
}

export function Card({
  children,
  style,
  onPress,
  variant = 'default',
}: CardProps) {
  const Container = onPress ? TouchableOpacity : View;

  return (
    <Container
      style={[styles.base, styles[variant], style]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      {children}
    </Container>
  );
}

interface AlertCardProps {
  severity: string;
  title: string;
  description?: string;
  location?: string;
  time?: string;
  onPress?: () => void;
  style?: ViewStyle;
}

export function AlertCard({
  severity,
  title,
  description,
  location,
  time,
  onPress,
  style,
}: AlertCardProps) {
  const { t } = useLanguage();
  const bgColor = severity === 'critical' || severity === 'high'
    ? colors.primary
    : severity === 'medium'
      ? colors.warning
      : colors.info;

  return (
    <TouchableOpacity
      style={[styles.alertCard, { backgroundColor: bgColor }, style]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      <View style={styles.alertHeader}>
        <Text style={styles.alertBadge}>{t('alertCard.severeWeatherAlert')}</Text>
      </View>
      <Text style={styles.alertTitle}>{title}</Text>
      {(location || time) && (
        <View style={styles.alertMeta}>
          {location && <Text style={styles.alertLocation}>{location}</Text>}
          {time && <Text style={styles.alertTime}>{time}</Text>}
        </View>
      )}
      {description && <Text style={styles.alertDescription}>{description}</Text>}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  base: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
  },
  default: {
    ...shadows.low,
  },
  elevated: {
    ...shadows.medium,
  },
  outlined: {
    borderWidth: 1,
    borderColor: colors.border,
  },
  alertCard: {
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    marginHorizontal: spacing.base,
    marginVertical: spacing.sm,
  },
  alertHeader: {
    marginBottom: spacing.sm,
  },
  alertBadge: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.white,
    backgroundColor: 'rgba(255,255,255,0.25)',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xxs,
    borderRadius: borderRadius.sm,
    alignSelf: 'flex-start',
    overflow: 'hidden',
  },
  alertTitle: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.white,
    marginBottom: spacing.xs,
  },
  alertMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.xs,
  },
  alertLocation: {
    fontSize: typography.fontSize.sm,
    color: colors.white,
    opacity: 0.9,
  },
  alertTime: {
    fontSize: typography.fontSize.sm,
    color: colors.white,
    opacity: 0.7,
  },
  alertDescription: {
    fontSize: typography.fontSize.sm,
    color: colors.white,
    opacity: 0.85,
    lineHeight: 20,
  },
});
