import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LoadingState, ErrorState } from '../../components/LoadingState';
import { colors } from '../../theme/colors';
import { typography, spacing, borderRadius } from '../../theme';
import { shadows } from '../../theme/shadows';
import { getReliefResource } from '../../services/api/operationsApi';
import { useLanguage, type TranslationKey } from '../../i18n';
import type { ReliefResource } from '../../services/api/operationsApi';

interface ReliefResourceDetailScreenProps {
  navigation: any;
  route: { params: { id: string } };
}

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  available: { bg: colors.successLight, text: colors.success },
  allocated: { bg: colors.infoLight, text: colors.info },
  depleted: { bg: colors.errorLight, text: colors.error },
  expired: { bg: colors.backgroundGray, text: colors.textLight },
};

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleString();
}

export function ReliefResourceDetailScreen({ navigation, route }: ReliefResourceDetailScreenProps) {
  const { id } = route.params;
  const { t } = useLanguage();
  const [resource, setResource] = useState<ReliefResource | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const statusLabelKey = (status: string): TranslationKey =>
    `operations.statuses.${status}` as TranslationKey;

  const fetchData = useCallback(async () => {
    const result = await getReliefResource(id);
    if (result.success && result.data) {
      setResource(result.data);
      setError(null);
    } else {
      setError(result.error?.message || t('operations.resources.notFound'));
    }
  }, [id, t]);

  useEffect(() => {
    fetchData().finally(() => setLoading(false));
  }, [fetchData]);

  if (loading) {
    return <LoadingState message={t('operations.resources.loadingDetail')} />;
  }

  if (error || !resource) {
    return (
      <ErrorState
        message={error || t('operations.resources.notFound')}
        onRetry={fetchData}
      />
    );
  }

  const sc = STATUS_COLORS[resource.status] || { bg: colors.backgroundGray, text: colors.textLight };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('operations.resources.detailTitle')}</Text>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
      >
        <View style={[styles.statusCard, { backgroundColor: sc.bg }]}>
          <View style={[styles.statusDot, { backgroundColor: sc.text }]} />
          <Text style={[styles.statusText, { color: sc.text }]}>
            {t(statusLabelKey(resource.status))}
          </Text>
        </View>

        <View style={[styles.infoCard, shadows.low]}>
          <Text style={styles.cardSectionTitle}>{t('operations.resources.infoTitle')}</Text>
          <InfoRow label={t('operations.resources.id')} value={resource.id} truncate />
          <InfoRow label={t('operations.resources.type')} value={resource.resource_type} capitalize />
          {resource.description && <InfoRow label={t('operations.resources.description')} value={resource.description} />}
          <InfoRow label={t('operations.resources.created')} value={formatDate(resource.created_at)} />
          <InfoRow label={t('operations.resources.updated')} value={formatDate(resource.updated_at)} />
        </View>

        <View style={[styles.infoCard, shadows.low]}>
          <Text style={styles.cardSectionTitle}>{t('operations.resources.quantityTitle')}</Text>
          <InfoRow
            label={t('operations.resources.total')}
            value={resource.quantity != null ? `${resource.quantity}${resource.unit ? ` ${resource.unit}` : ''}` : '—'}
          />
          <InfoRow
            label={t('operations.resources.available')}
            value={resource.available_quantity != null ? `${resource.available_quantity}${resource.unit ? ` ${resource.unit}` : ''}` : '—'}
          />
          {resource.unit && <InfoRow label={t('operations.resources.unit')} value={resource.unit} />}
        </View>

        <View style={[styles.infoCard, shadows.low]}>
          <Text style={styles.cardSectionTitle}>{t('operations.resources.providerTitle')}</Text>
          <InfoRow label={t('operations.resources.providerId')} value={resource.provider_id || '—'} truncate />
        </View>
      </ScrollView>
    </View>
  );
}

function InfoRow({
  label,
  value,
  capitalize,
  truncate,
}: {
  label: string;
  value: string;
  capitalize?: boolean;
  truncate?: boolean;
}) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text
        style={[styles.infoValue, capitalize && styles.capitalize]}
        numberOfLines={truncate ? 1 : undefined}
        ellipsizeMode={truncate ? 'tail' : undefined}
      >
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.backgroundLight,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.base,
    paddingTop: spacing.xl,
    paddingBottom: spacing.base,
  },
  backBtn: {
    marginRight: spacing.md,
  },
  headerTitle: {
    flex: 1,
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
  },
  content: {
    paddingHorizontal: spacing.base,
    paddingBottom: 20,
    gap: spacing.md,
  },
  statusCard: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: borderRadius.lg,
    padding: spacing.base,
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: spacing.sm,
  },
  statusText: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
  },
  infoCard: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
  },
  cardSectionTitle: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.textSecondary,
    marginBottom: spacing.md,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
  },
  infoLabel: {
    fontSize: typography.fontSize.md,
    color: colors.textSecondary,
  },
  infoValue: {
    fontSize: typography.fontSize.md,
    color: colors.text,
    fontWeight: typography.fontWeight.medium,
    maxWidth: '60%',
    textAlign: 'right',
  },
  capitalize: {
    textTransform: 'capitalize',
  },
});
