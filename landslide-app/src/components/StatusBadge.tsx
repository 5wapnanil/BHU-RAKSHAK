import React from 'react';
import { Text, StyleSheet, ViewStyle } from 'react-native';
import { colors } from '../theme/colors';
import { borderRadius, spacing, typography } from '../theme';
import { useLanguage, type TranslationKey } from '../i18n';

type BadgeStatus = 'pending' | 'in_progress' | 'resolved' | 'cancelled' | 'critical' | 'high' | 'medium' | 'low';

interface StatusBadgeProps {
  status: BadgeStatus;
  label?: string;
  style?: ViewStyle;
}

const statusConfig: Record<BadgeStatus, { bg: string; text: string; defaultLabelKey: TranslationKey }> = {
  pending: { bg: colors.warningLight, text: colors.warning, defaultLabelKey: 'myRequests.statuses.pending' },
  in_progress: { bg: colors.infoLight, text: colors.info, defaultLabelKey: 'myRequests.statuses.inProgress' },
  resolved: { bg: colors.successLight, text: colors.success, defaultLabelKey: 'myRequests.statuses.resolved' },
  cancelled: { bg: colors.backgroundGray, text: colors.textLight, defaultLabelKey: 'myRequests.statuses.cancelled' },
  critical: { bg: colors.errorLight, text: colors.error, defaultLabelKey: 'alerts.filters.critical' },
  high: { bg: colors.errorLight, text: colors.error, defaultLabelKey: 'alerts.filters.high' },
  medium: { bg: colors.warningLight, text: colors.warning, defaultLabelKey: 'alerts.filters.medium' },
  low: { bg: colors.successLight, text: colors.success, defaultLabelKey: 'alerts.filters.low' },
};

export function StatusBadge({ status, label, style }: StatusBadgeProps) {
  const { t } = useLanguage();
  const config = statusConfig[status] || statusConfig.pending;

  return (
    <Text style={[styles.badge, { backgroundColor: config.bg, color: config.text }, style]}>
      {label || t(config.defaultLabelKey)}
    </Text>
  );
}

const styles = StyleSheet.create({
  badge: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.semiBold,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xxs,
    borderRadius: borderRadius.round,
    alignSelf: 'flex-start',
    overflow: 'hidden',
  },
});
