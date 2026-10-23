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
import { Card, StatusBadge } from '../../components';
import { LoadingState, EmptyState, ErrorState } from '../../components/LoadingState';
import { colors } from '../../theme/colors';
import { typography, spacing, borderRadius } from '../../theme';
import { shadows } from '../../theme/shadows';
import { getAssignments } from '../../services/api/operationsApi';
import { useLanguage, type TranslationKey } from '../../i18n';
import type { Assignment } from '../../services/api/operationsApi';

interface AssignmentsScreenProps {
  navigation: any;
}

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  pending: { bg: colors.warningLight, text: colors.warning },
  created: { bg: colors.infoLight, text: colors.info },
  accepted: { bg: colors.successLight, text: colors.success },
  in_progress: { bg: colors.infoLight, text: colors.info },
  started: { bg: colors.infoLight, text: colors.info },
  completed: { bg: colors.successLight, text: colors.success },
  cancelled: { bg: colors.backgroundGray, text: colors.textLight },
  rejected: { bg: colors.errorLight, text: colors.error },
};

function getStatusColor(status: string) {
  return STATUS_COLORS[status] || { bg: colors.backgroundGray, text: colors.textLight };
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function AssignmentsScreen({ navigation }: AssignmentsScreenProps) {
  const { t } = useLanguage();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    const result = await getAssignments(200);
    if (result.success && result.data) {
      setAssignments(result.data);
      setError(null);
    } else {
      setError(result.error?.message || t('operations.assignments.error'));
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

  const statusLabelKey = (status: string): TranslationKey =>
    `operations.statuses.${status}` as TranslationKey;

  if (loading) {
    return <LoadingState message={t('operations.assignments.loading')} />;
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
        <Text style={styles.headerTitle}>{t('operations.assignments.title')}</Text>
        <View style={styles.headerRight}>
          <Text style={styles.countBadge}>{assignments.length}</Text>
        </View>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.listContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
      >
        {assignments.length === 0 ? (
          <EmptyState
            icon="clipboard-outline"
            title={t('operations.assignments.empty')}
            description={t('operations.assignments.emptyDesc')}
          />
        ) : (
          assignments.map((a) => {
            const sc = getStatusColor(a.status);
            return (
              <TouchableOpacity
                key={a.id}
                style={[styles.card, shadows.low]}
                onPress={() => navigation.navigate('AssignmentDetail', { id: a.id })}
                activeOpacity={0.7}
              >
                <View style={styles.cardHeader}>
                  <View style={[styles.statusDot, { backgroundColor: sc.text }]} />
                  <Text style={[styles.statusText, { color: sc.text }]}>
                    {t(statusLabelKey(a.status))}
                  </Text>
                  <Text style={styles.dateText}>{formatDate(a.created_at)}</Text>
                </View>

                <Text style={styles.cardTitle}>
                  {a.assignment_type
                    ? a.assignment_type.replace(/_/g, ' ')
                    : t('operations.assignments.defaultTitle')}
                </Text>

                <View style={styles.cardMeta}>
                  {a.volunteer_id && (
                    <View style={styles.metaItem}>
                      <Ionicons name="person-outline" size={14} color={colors.textSecondary} />
                      <Text style={styles.metaText}>
                        {t('operations.assignments.volunteerLabel', {
                          id: `${a.volunteer_id.substring(0, 8)}...`,
                        })}
                      </Text>
                    </View>
                  )}
                  {a.request_id && (
                    <View style={styles.metaItem}>
                      <Ionicons name="document-text-outline" size={14} color={colors.textSecondary} />
                      <Text style={styles.metaText}>
                        {t('operations.assignments.requestLabel', {
                          id: `${a.request_id.substring(0, 8)}...`,
                        })}
                      </Text>
                    </View>
                  )}
                </View>

                {a.notes && (
                  <Text style={styles.notesText} numberOfLines={1}>
                    {a.notes}
                  </Text>
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
  dateText: {
    fontSize: typography.fontSize.xs,
    color: colors.textLight,
  },
  cardTitle: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    marginBottom: spacing.sm,
    textTransform: 'capitalize',
  },
  cardMeta: {
    gap: spacing.xs,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  metaText: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
  },
  notesText: {
    fontSize: typography.fontSize.sm,
    color: colors.textLight,
    marginTop: spacing.sm,
    fontStyle: 'italic',
  },
});
