import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LoadingState, EmptyState, ErrorState } from '../../components/LoadingState';
import { colors } from '../../theme/colors';
import { typography, spacing, borderRadius } from '../../theme';
import { shadows } from '../../theme/shadows';
import { getReliefResources } from '../../services/api/operationsApi';
import { useLanguage, type TranslationKey } from '../../i18n';
import type { ReliefResource } from '../../services/api/operationsApi';

interface ReliefResourcesScreenProps {
  navigation: any;
}

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  available: { bg: colors.successLight, text: colors.success },
  allocated: { bg: colors.infoLight, text: colors.info },
  depleted: { bg: colors.errorLight, text: colors.error },
  expired: { bg: colors.backgroundGray, text: colors.textLight },
};

function getStatusColor(status: string) {
  return STATUS_COLORS[status] || { bg: colors.backgroundGray, text: colors.textLight };
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function ReliefResourcesScreen({ navigation }: ReliefResourcesScreenProps) {
  const { t } = useLanguage();
  const [resources, setResources] = useState<ReliefResource[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    const result = await getReliefResources(200);
    if (result.success && result.data) {
      setResources(result.data);
      setError(null);
    } else {
      setError(result.error?.message || t('operations.resources.error'));
    }
  }, [t]);

  useEffect(() => {
    fetchData().finally(() => setLoading(false));
  }, [fetchData]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  }, [fetchData]);

  const statusLabelKey = (status: string): TranslationKey => {
    return `operations.statuses.${status}` as TranslationKey;
  };

  if (loading) {
    return <LoadingState message={t('operations.resources.loading')} />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('operations.resources.title')}</Text>
        <View style={styles.headerRight}>
          <Text style={styles.countBadge}>{resources.length}</Text>
        </View>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.listContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
      >
        {resources.length === 0 ? (
          <EmptyState
            icon="medical-outline"
            title={t('operations.resources.empty')}
            description={t('operations.resources.emptyDesc')}
          />
        ) : (
          resources.map((r) => {
            const sc = getStatusColor(r.status);
            return (
              <TouchableOpacity
                key={r.id}
                style={[styles.card, shadows.low]}
                onPress={() => navigation.navigate('ReliefResourceDetail', { id: r.id })}
                activeOpacity={0.7}
              >
                <View style={styles.cardHeader}>
                  <View style={[styles.statusDot, { backgroundColor: sc.text }]} />
                  <Text style={[styles.statusText, { color: sc.text }]}>
                    {t(statusLabelKey(r.status))}
                  </Text>
                  <Text style={styles.dateText}>{formatDate(r.created_at)}</Text>
                </View>

                <Text style={styles.cardTitle}>{r.resource_type}</Text>

                {r.description && (
                  <Text style={styles.descText} numberOfLines={1}>
                    {r.description}
                  </Text>
                )}

                <View style={styles.quantityRow}>
                  {r.quantity != null && (
                    <View style={styles.quantityItem}>
                      <Text style={styles.quantityLabel}>{t('operations.resources.qty')}</Text>
                      <Text style={styles.quantityValue}>
                        {r.quantity}{r.unit ? ` ${r.unit}` : ''}
                      </Text>
                    </View>
                  )}
                  {r.available_quantity != null && (
                    <View style={styles.quantityItem}>
                      <Text style={styles.quantityLabel}>{t('operations.resources.available')}</Text>
                      <Text style={[styles.quantityValue, r.available_quantity <= 0 && styles.depleted]}>
                        {r.available_quantity}{r.unit ? ` ${r.unit}` : ''}
                      </Text>
                    </View>
                  )}
                </View>
              </TouchableOpacity>
            );
          })
        )}
      </ScrollView>
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
  headerRight: {
    alignItems: 'flex-end',
  },
  countBadge: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.primary,
    backgroundColor: colors.primary + '15',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xxs,
    borderRadius: borderRadius.round,
    overflow: 'hidden',
  },
  listContent: {
    paddingHorizontal: spacing.base,
    paddingBottom: 20,
    gap: spacing.md,
  },
  card: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: spacing.sm,
  },
  statusText: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.semiBold,
    flex: 1,
  },
  dateText: {
    fontSize: typography.fontSize.xs,
    color: colors.textLight,
  },
  cardTitle: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    marginBottom: spacing.xs,
    textTransform: 'capitalize',
  },
  descText: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  quantityRow: {
    flexDirection: 'row',
    gap: spacing.xl,
  },
  quantityItem: {
    gap: spacing.xxs,
  },
  quantityLabel: {
    fontSize: typography.fontSize.xs,
    color: colors.textLight,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  quantityValue: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  depleted: {
    color: colors.error,
  },
});
