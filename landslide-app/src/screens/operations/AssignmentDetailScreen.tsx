import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LoadingState, ErrorState } from '../../components/LoadingState';
import { colors } from '../../theme/colors';
import { typography, spacing, borderRadius } from '../../theme';
import { shadows } from '../../theme/shadows';
import { getAssignment, updateAssignmentStatus } from '../../services/api/operationsApi';
import { useLanguage, type TranslationKey } from '../../i18n';
import type { Assignment } from '../../services/api/operationsApi';

interface AssignmentDetailScreenProps {
  navigation: any;
  route: { params: { id: string } };
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

const VALID_TRANSITIONS: Record<string, string[]> = {
  pending: ['accepted', 'rejected', 'cancelled'],
  created: ['accepted', 'cancelled'],
  accepted: ['started', 'in_progress', 'cancelled'],
  started: ['completed', 'cancelled'],
  in_progress: ['completed', 'cancelled'],
};

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleString();
}

export function AssignmentDetailScreen({ navigation, route }: AssignmentDetailScreenProps) {
  const { id } = route.params;
  const { t } = useLanguage();
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const statusLabelKey = (status: string): TranslationKey =>
    `operations.statuses.${status}` as TranslationKey;

  const fetchData = useCallback(async () => {
    const result = await getAssignment(id);
    if (result.success && result.data) {
      setAssignment(result.data);
      setError(null);
    } else {
      setError(result.error?.message || t('operations.assignments.notFound'));
    }
  }, [id, t]);

  useEffect(() => {
    fetchData().finally(() => setLoading(false));
  }, [fetchData]);

  const handleStatusChange = async (newStatus: string) => {
    if (!assignment) return;
    Alert.alert(
      t('operations.assignments.updateStatusTitle'),
      t('operations.assignments.updateStatusMessage', {
        status: t(statusLabelKey(newStatus)),
      }),
      [
        { text: t('common.cancel'), style: 'cancel' },
        {
          text: t('operations.assignments.confirm'),
          onPress: async () => {
            setUpdating(true);
            const result = await updateAssignmentStatus(assignment.id, newStatus);
            if (result.success && result.data) {
              setAssignment(result.data);
            } else {
              Alert.alert(
                t('common.error'),
                result.error?.message || t('operations.assignments.updateError'),
              );
            }
            setUpdating(false);
          },
        },
      ],
    );
  };

  if (loading) {
    return <LoadingState message={t('operations.assignments.loadingDetail')} />;
  }

  if (error || !assignment) {
    return (
      <ErrorState
        message={error || t('operations.assignments.notFound')}
        onRetry={fetchData}
      />
    );
  }

  const sc = STATUS_COLORS[assignment.status] || { bg: colors.backgroundGray, text: colors.textLight };
  const transitions = VALID_TRANSITIONS[assignment.status] || [];

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('operations.assignments.detailTitle')}</Text>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
      >
        <View style={[styles.statusCard, { backgroundColor: sc.bg }]}>
          <View style={[styles.statusDot, { backgroundColor: sc.text }]} />
          <Text style={[styles.statusText, { color: sc.text }]}>
            {t(statusLabelKey(assignment.status))}
          </Text>
        </View>

        <View style={[styles.infoCard, shadows.low]}>
          <Text style={styles.cardSectionTitle}>{t('operations.assignments.infoTitle')}</Text>

          <InfoRow label={t('operations.assignments.id')} value={assignment.id} />
          <InfoRow label={t('operations.assignments.type')} value={assignment.assignment_type?.replace(/_/g, ' ') || '—'} capitalize />
          <InfoRow label={t('operations.assignments.created')} value={formatDate(assignment.created_at)} />
          <InfoRow label={t('operations.assignments.updated')} value={formatDate(assignment.updated_at)} />
        </View>

        <View style={[styles.infoCard, shadows.low]}>
          <Text style={styles.cardSectionTitle}>{t('operations.assignments.referencesTitle')}</Text>
          <InfoRow label={t('operations.assignments.volunteerId')} value={assignment.volunteer_id || '—'} truncate />
          <InfoRow label={t('operations.assignments.requestId')} value={assignment.request_id || '—'} truncate />
          <InfoRow label={t('operations.assignments.resourceId')} value={assignment.resource_id || '—'} truncate />
        </View>

        {assignment.notes && (
          <View style={[styles.infoCard, shadows.low]}>
            <Text style={styles.cardSectionTitle}>{t('operations.assignments.notesTitle')}</Text>
            <Text style={styles.notesText}>{assignment.notes}</Text>
          </View>
        )}

        {transitions.length > 0 && (
          <View style={[styles.infoCard, shadows.low]}>
            <Text style={styles.cardSectionTitle}>{t('operations.assignments.actionsTitle')}</Text>
            <View style={styles.actionsGrid}>
              {transitions.map((status) => (
                <TouchableOpacity
                  key={status}
                  style={[styles.actionBtn, updating && styles.actionBtnDisabled]}
                  onPress={() => handleStatusChange(status)}
                  disabled={updating}
                  activeOpacity={0.7}
                >
                  <Text style={styles.actionBtnText}>
                    {t(statusLabelKey(status))}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}
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
  notesText: {
    fontSize: typography.fontSize.md,
    color: colors.text,
    lineHeight: 20,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  actionBtn: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
  },
  actionBtnDisabled: {
    opacity: 0.5,
  },
  actionBtnText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.white,
  },
});
