import React, { useState, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { LoadingState, EmptyState, ErrorState } from '../../components/LoadingState';
import { colors } from '../../theme/colors';
import { typography, spacing, borderRadius } from '../../theme';
import { shadows } from '../../theme/shadows';
import { getShelters } from '../../services/api/operationsApi';
import { useLanguage, type TranslationKey } from '../../i18n';
import type { Shelter } from '../../services/api/operationsApi';

interface SheltersScreenProps {
  navigation: any;
}

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  open: { bg: colors.successLight, text: colors.success },
  full: { bg: colors.warningLight, text: colors.warning },
  closed: { bg: colors.errorLight, text: colors.error },
};

function getStatusColor(status: string) {
  return STATUS_COLORS[status] || { bg: colors.backgroundGray, text: colors.textLight };
}

function getOccupancyColor(current: number, capacity: number): string {
  if (capacity <= 0) return colors.textLight;
  if (current > capacity) return colors.error;
  const pct = current / capacity;
  if (pct >= 0.9) return colors.error;
  if (pct >= 0.7) return colors.warning;
  return colors.success;
}

export function SheltersScreen({ navigation }: SheltersScreenProps) {
  const { t } = useLanguage();
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const requestIdRef = useRef(0);
  const hasLoadedRef = useRef(false);

  const statusLabelKey = (status: string): TranslationKey =>
    `operations.statuses.${status}` as TranslationKey;

  const fetchData = useCallback(
    async (isBackground = false) => {
      const reqId = ++requestIdRef.current;
      try {
        const result = await getShelters(200);
        if (reqId !== requestIdRef.current) return;

        if (result.success && result.data) {
          setShelters(result.data);
          hasLoadedRef.current = true;
          setError(null);
        } else {
          if (!isBackground || !hasLoadedRef.current) {
            setError(result.error?.message || t('operations.shelters.error'));
          }
        }
      } catch {
        if (reqId !== requestIdRef.current) return;
        if (!isBackground || !hasLoadedRef.current) {
          setError(t('operations.shelters.error'));
        }
      } finally {
        if (reqId === requestIdRef.current) {
          setLoading(false);
        }
      }
    },
    [t]
  );

  useFocusEffect(
    useCallback(() => {
      fetchData(true);
      return () => {
        requestIdRef.current++;
      };
    }, [fetchData])
  );

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await fetchData(false);
    } finally {
      setRefreshing(false);
    }
  }, [fetchData]);

  const handleRetry = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchData(false);
  }, [fetchData]);

  if (loading) {
    return <LoadingState message={t('operations.shelters.loading')} />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={handleRetry} />;
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('operations.shelters.title')}</Text>
        <View style={styles.headerRight}>
          <Text style={styles.countBadge}>{shelters.length}</Text>
        </View>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.listContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
      >
        {shelters.length === 0 ? (
          <EmptyState
            icon="home-outline"
            title={t('operations.shelters.empty')}
            description={t('operations.shelters.emptyDesc')}
          />
        ) : (
          shelters.map((s) => {
            const sc = getStatusColor(s.status);
            const hasPositiveCapacity = s.capacity > 0;
            const isOverCapacity = hasPositiveCapacity && s.current_occupancy > s.capacity;
            const occupancyPct = hasPositiveCapacity
              ? Math.round((s.current_occupancy / s.capacity) * 100)
              : 0;
            const barColor = getOccupancyColor(s.current_occupancy, s.capacity);
            return (
              <TouchableOpacity
                key={s.id}
                style={[styles.card, shadows.low]}
                onPress={() => navigation.navigate('ShelterDetail', { id: s.id })}
                activeOpacity={0.7}
              >
                <View style={styles.cardHeader}>
                  <View style={[styles.statusDot, { backgroundColor: sc.text }]} />
                  <Text style={[styles.statusText, { color: sc.text }]}>
                    {t(statusLabelKey(s.status))}
                  </Text>
                </View>

                <Text style={styles.cardTitle}>{s.name}</Text>

                {s.address && (
                  <Text style={styles.addressText} numberOfLines={1}>
                    {s.address}
                  </Text>
                )}

                <View style={styles.capacitySection}>
                  <View style={styles.capacityHeader}>
                    <View style={styles.capacityLabelContainer}>
                      <Text style={styles.capacityLabel}>{t('operations.shelters.capacity')}</Text>
                      {isOverCapacity && (
                        <View style={styles.overCapacityBadge}>
                          <Text style={styles.overCapacityBadgeText}>
                            {t('operations.shelters.overCapacity')}
                          </Text>
                        </View>
                      )}
                    </View>
                    <Text
                      style={[
                        styles.capacityValue,
                        isOverCapacity && styles.overCapacityValue,
                      ]}
                    >
                      {s.current_occupancy} / {s.capacity}
                    </Text>
                  </View>
                  <View style={styles.progressBg}>
                    <View
                      style={[
                        styles.progressBar,
                        {
                          width: `${hasPositiveCapacity ? Math.min(occupancyPct, 100) : 0}%`,
                          backgroundColor: barColor,
                        },
                      ]}
                    />
                  </View>
                  <Text style={[styles.capacityPct, { color: isOverCapacity ? colors.error : barColor }]}>
                    {!hasPositiveCapacity
                      ? t('operations.shelters.noCapacity')
                      : isOverCapacity
                        ? t('operations.shelters.overCapacityPct', { pct: occupancyPct })
                        : t('operations.shelters.occupied', { pct: occupancyPct })}
                  </Text>
                </View>

                {s.contact_phone && (
                  <View style={styles.phoneRow}>
                    <Ionicons name="call-outline" size={14} color={colors.textSecondary} />
                    <Text style={styles.phoneText}>{s.contact_phone}</Text>
                  </View>
                )}
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
  cardTitle: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  addressText: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  capacitySection: {
    marginBottom: spacing.sm,
  },
  capacityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  capacityLabelContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  capacityLabel: {
    fontSize: typography.fontSize.xs,
    color: colors.textLight,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  overCapacityBadge: {
    backgroundColor: colors.errorLight,
    paddingHorizontal: spacing.xs,
    paddingVertical: 1,
    borderRadius: borderRadius.xs,
  },
  overCapacityBadgeText: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.bold,
    color: colors.error,
    textTransform: 'uppercase',
  },
  capacityValue: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  overCapacityValue: {
    color: colors.error,
  },
  progressBg: {
    height: 6,
    backgroundColor: colors.backgroundGray,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    borderRadius: 3,
  },
  capacityPct: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.semiBold,
    marginTop: spacing.xxs,
  },
  phoneRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  phoneText: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
  },
});
