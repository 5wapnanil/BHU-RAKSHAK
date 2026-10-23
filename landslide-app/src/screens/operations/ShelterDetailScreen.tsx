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
import { getShelter } from '../../services/api/operationsApi';
import { useLanguage, type TranslationKey } from '../../i18n';
import type { Shelter } from '../../services/api/operationsApi';

interface ShelterDetailScreenProps {
  navigation: any;
  route: { params: { id: string } };
}

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  open: { bg: colors.successLight, text: colors.success },
  full: { bg: colors.warningLight, text: colors.warning },
  closed: { bg: colors.errorLight, text: colors.error },
};

function getOccupancyColor(current: number, capacity: number): string {
  if (capacity <= 0) return colors.textLight;
  const pct = current / capacity;
  if (pct >= 0.9) return colors.error;
  if (pct >= 0.7) return colors.warning;
  return colors.success;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleString();
}

export function ShelterDetailScreen({ navigation, route }: ShelterDetailScreenProps) {
  const { id } = route.params;
  const { t } = useLanguage();
  const [shelter, setShelter] = useState<Shelter | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const statusLabelKey = (status: string): TranslationKey =>
    `operations.statuses.${status}` as TranslationKey;

  const fetchData = useCallback(async () => {
    const result = await getShelter(id);
    if (result.success && result.data) {
      setShelter(result.data);
      setError(null);
    } else {
      setError(result.error?.message || t('operations.shelters.notFound'));
    }
  }, [id, t]);

  useEffect(() => {
    fetchData().finally(() => setLoading(false));
  }, [fetchData]);

  if (loading) {
    return <LoadingState message={t('operations.shelters.loadingDetail')} />;
  }

  if (error || !shelter) {
    return (
      <ErrorState
        message={error || t('operations.shelters.notFound')}
        onRetry={fetchData}
      />
    );
  }

  const sc = STATUS_COLORS[shelter.status] || { bg: colors.backgroundGray, text: colors.textLight };
  const occupancyPct = shelter.capacity > 0 ? Math.round((shelter.current_occupancy / shelter.capacity) * 100) : 0;
  const barColor = getOccupancyColor(shelter.current_occupancy, shelter.capacity);
  const available = shelter.capacity - shelter.current_occupancy;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('operations.shelters.detailTitle')}</Text>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
      >
        <View style={[styles.statusCard, { backgroundColor: sc.bg }]}>
          <View style={[styles.statusDot, { backgroundColor: sc.text }]} />
          <Text style={[styles.statusText, { color: sc.text }]}>
            {t(statusLabelKey(shelter.status))}
          </Text>
        </View>

        <View style={[styles.infoCard, shadows.low]}>
          <Text style={styles.cardSectionTitle}>{t('operations.shelters.infoTitle')}</Text>
          <InfoRow label={t('operations.shelters.name')} value={shelter.name} />
          <InfoRow label={t('operations.shelters.id')} value={shelter.id} truncate />
          {shelter.address && <InfoRow label={t('operations.shelters.address')} value={shelter.address} />}
          <InfoRow label={t('operations.shelters.created')} value={formatDate(shelter.created_at)} />
          <InfoRow label={t('operations.shelters.updated')} value={formatDate(shelter.updated_at)} />
        </View>

        <View style={[styles.infoCard, shadows.low]}>
          <Text style={styles.cardSectionTitle}>{t('operations.shelters.capacityTitle')}</Text>
          <View style={styles.capacityOverview}>
            <View style={styles.capacityBig}>
              <Text style={[styles.capacityBigNum, { color: barColor }]}>
                {shelter.current_occupancy}
              </Text>
              <Text style={styles.capacityBigLabel}>{t('operations.shelters.current')}</Text>
            </View>
            <Text style={styles.capacitySlash}>/</Text>
            <View style={styles.capacityBig}>
              <Text style={styles.capacityBigNum}>{shelter.capacity}</Text>
              <Text style={styles.capacityBigLabel}>{t('operations.shelters.capacity')}</Text>
            </View>
          </View>

          <View style={styles.progressBg}>
            <View
              style={[
                styles.progressBar,
                {
                  width: `${Math.min(occupancyPct, 100)}%`,
                  backgroundColor: barColor,
                },
              ]}
            />
          </View>
          <Text style={[styles.capacityPct, { color: barColor }]}>
            {t('operations.shelters.occupied', { pct: occupancyPct })} — {t('operations.shelters.spotsAvailable', { count: available >= 0 ? available : 0 })}
          </Text>
        </View>

        <View style={[styles.infoCard, shadows.low]}>
          <Text style={styles.cardSectionTitle}>{t('operations.shelters.contactTitle')}</Text>
          <InfoRow label={t('operations.shelters.phone')} value={shelter.contact_phone || '—'} />
          <InfoRow label={t('operations.shelters.operatedBy')} value={shelter.operated_by || '—'} truncate />
        </View>

        {shelter.location && (
          <View style={[styles.infoCard, shadows.low]}>
            <Text style={styles.cardSectionTitle}>{t('operations.shelters.locationTitle')}</Text>
            <InfoRow label={t('operations.shelters.coordinates')} value={shelter.location} />
          </View>
        )}

        {shelter.facilities && Object.keys(shelter.facilities).length > 0 && (
          <View style={[styles.infoCard, shadows.low]}>
            <Text style={styles.cardSectionTitle}>{t('operations.shelters.facilitiesTitle')}</Text>
            {Object.entries(shelter.facilities).map(([key, val]) => (
              <InfoRow key={key} label={key.replace(/_/g, ' ')} value={String(val)} />
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

function InfoRow({
  label,
  value,
  truncate,
}: {
  label: string;
  value: string;
  truncate?: boolean;
}) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text
        style={styles.infoValue}
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
    textTransform: 'capitalize',
  },
  infoValue: {
    fontSize: typography.fontSize.md,
    color: colors.text,
    fontWeight: typography.fontWeight.medium,
    maxWidth: '60%',
    textAlign: 'right',
  },
  capacityOverview: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.base,
  },
  capacityBig: {
    alignItems: 'center',
  },
  capacityBigNum: {
    fontSize: typography.fontSize.xxxl,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
  },
  capacityBigLabel: {
    fontSize: typography.fontSize.xs,
    color: colors.textLight,
    textTransform: 'uppercase',
  },
  capacitySlash: {
    fontSize: typography.fontSize.xxl,
    color: colors.textLight,
    marginHorizontal: spacing.md,
  },
  progressBg: {
    height: 8,
    backgroundColor: colors.backgroundGray,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    borderRadius: 4,
  },
  capacityPct: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    marginTop: spacing.sm,
    textAlign: 'center',
  },
});
