import React, { useState, useEffect, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Card, StatusBadge } from '../components';
import { LoadingState, EmptyState } from '../components/LoadingState';
import { colors } from '../theme/colors';
import { typography, spacing, borderRadius } from '../theme';
import { useLocalRequests } from '../hooks/useLocalRequests';
import { useLanguage, type TranslationKey } from '../i18n';
import type { LocalRequest, RequestType, RequestStatus } from '../types';

interface MyRequestsScreenProps {
  navigation: any;
}

interface RequestItem {
  id: string;
  type: RequestType;
  status: RequestStatus;
  syncStatus?: import('../types').SyncStatus;
  titleKey?: TranslationKey;
  title?: string;
  descriptionKey?: TranslationKey;
  description?: string;
  location: string;
  dateKey?: TranslationKey;
  date?: string;
  time: string;
  severity: string;
  responders?: number;
  titleParams?: Record<string, string | number>;
  descriptionParams?: Record<string, string | number>;
}

const MOCK_REQUESTS: RequestItem[] = [
  {
    id: 'REQ-2024-001',
    type: 'evacuation',
    status: 'in_progress',
    titleKey: 'myRequests.requestTypes.evacuation',
    titleParams: { location: 'Koramangala' },
    descriptionKey: 'myRequests.descriptions.familyTrapped',
    location: 'Koramangala Road, Block 4',
    dateKey: 'myRequests.times.today',
    time: '2:30 PM',
    severity: 'high',
    responders: 2,
  },
  {
    id: 'REQ-2024-002',
    type: 'help',
    status: 'pending',
    titleKey: 'myRequests.requestTypes.help',
    titleParams: { location: 'MG Road' },
    descriptionKey: 'myRequests.descriptions.elderlyStranded',
    location: 'MG Road, Near Central Market',
    dateKey: 'myRequests.times.today',
    time: '1:15 PM',
    severity: 'critical',
    responders: 0,
  },
  {
    id: 'REQ-2024-003',
    type: 'relief',
    status: 'resolved',
    titleKey: 'myRequests.requestTypes.reliefSupply',
    descriptionKey: 'myRequests.descriptions.foodWater25',
    location: 'HSR Layout Community Hall',
    dateKey: 'myRequests.times.yesterday',
    time: '6:45 PM',
    severity: 'medium',
    responders: 3,
  },
  {
    id: 'REQ-2024-004',
    type: 'volunteer',
    status: 'resolved',
    titleKey: 'myRequests.requestTypes.volunteerRegistration',
    descriptionKey: 'myRequests.descriptions.volunteerAvail',
    location: 'Srinagar Central',
    dateKey: 'myRequests.times.yesterday',
    time: '10:00 AM',
    severity: 'low',
    responders: 0,
  },
  {
    id: 'REQ-2024-005',
    type: 'help',
    status: 'cancelled',
    titleKey: 'myRequests.requestTypes.medicalHelp',
    descriptionKey: 'myRequests.descriptions.minorInjuries',
    location: 'Anantnag Main Bazaar',
    dateKey: 'myRequests.times.twoDays',
    time: '3:20 PM',
    severity: 'medium',
    responders: 0,
  },
  {
    id: 'REQ-2024-006',
    type: 'evacuation',
    status: 'resolved',
    titleKey: 'myRequests.requestTypes.communityEvacuation',
    descriptionKey: 'myRequests.descriptions.communityEvac',
    location: 'Pulwama District',
    dateKey: 'myRequests.times.threeDays',
    time: '8:00 AM',
    severity: 'high',
    responders: 4,
  },
];

const FILTERS: { key: string; labelKey: TranslationKey }[] = [
  { key: 'all', labelKey: 'myRequests.filters.all' },
  { key: 'pending', labelKey: 'myRequests.filters.pending' },
  { key: 'in_progress', labelKey: 'myRequests.filters.inProgress' },
  { key: 'resolved', labelKey: 'myRequests.filters.resolved' },
  { key: 'cancelled', labelKey: 'myRequests.filters.cancelled' },
];

function localRequestToItem(req: LocalRequest): RequestItem {
  const now = new Date(req.createdAt);
  const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  switch (req.type) {
    case 'evacuation':
      return {
        id: req.id,
        type: 'evacuation',
        status: req.status,
        titleKey: 'myRequests.requestTypes.evacuation',
        titleParams: { location: req.formData.location.split(',')[0] || 'Location' },
        descriptionKey: 'myRequests.descriptions.evacuation',
        descriptionParams: { count: req.formData.numberOfPeople, info: req.formData.additionalInfo || '' },
        location: req.formData.location,
        dateKey: 'myRequests.times.today',
        time: timeStr,
        severity: 'high',
      };
    case 'help':
      return {
        id: req.id,
        type: 'help',
        status: req.status,
        titleKey: 'myRequests.requestTypes.help',
        titleParams: { location: req.formData.location.split(',')[0] || 'Location' },
        description: req.formData.description || undefined,
        descriptionKey: req.formData.description ? undefined : 'myRequests.descriptions.helpDefault',
        descriptionParams: req.formData.description ? undefined : { severity: req.formData.severity || 'medium' },
        location: req.formData.location,
        dateKey: 'myRequests.times.today',
        time: timeStr,
        severity: req.formData.severity || 'medium',
      };
    case 'relief':
      return {
        id: req.id,
        type: 'relief',
        status: req.status,
        titleKey: 'myRequests.requestTypes.relief',
        titleParams: { location: req.formData.location.split(',')[0] || 'Location' },
        descriptionKey: 'myRequests.descriptions.relief',
        descriptionParams: {
          items: req.formData.requiredItems,
          count: req.formData.peopleAffected || 'multiple',
          info: req.formData.additionalInfo || '',
        },
        location: req.formData.location,
        dateKey: 'myRequests.times.today',
        time: timeStr,
        severity: req.formData.severity || 'medium',
      };
    case 'evacuation_volunteer':
      return {
        id: req.id,
        type: 'volunteer',
        status: req.status,
        titleKey: 'myRequests.requestTypes.evacuationVolunteer',
        descriptionKey: 'myRequests.descriptions.evacuationVolunteer',
        descriptionParams: {
          capabilities: req.formData.capabilities.join(', '),
          transport: req.formData.hasTransport ? 'Has vehicle.' : '',
        },
        location: req.formData.currentLocation,
        dateKey: 'myRequests.times.today',
        time: timeStr,
        severity: 'low',
      };
    case 'relief_volunteer':
      return {
        id: req.id,
        type: 'volunteer',
        status: req.status,
        syncStatus: req.syncStatus,
        titleKey: 'myRequests.requestTypes.reliefVolunteer',
        descriptionKey: 'myRequests.descriptions.reliefVolunteer',
        descriptionParams: {
          category: req.formData.category,
          description: req.formData.description || '',
        },
        location: req.formData.location,
        dateKey: 'myRequests.times.today',
        time: timeStr,
        severity: 'low',
      };
    case 'field_report':
      return {
        id: req.id,
        type: 'field_report',
        status: req.status,
        syncStatus: req.syncStatus,
        title: req.formData.locationName ? `Field Report: ${req.formData.locationName}` : 'Field Intelligence Report',
        description: req.formData.notes || (req.formData.photoUri ? 'Field photograph attached.' : 'Field observation report.'),
        location: req.formData.locationName || (req.formData.gpsCoords ? `GPS (${req.formData.gpsCoords.latitude.toFixed(4)}, ${req.formData.gpsCoords.longitude.toFixed(4)})` : 'Unspecified Coordinates'),
        dateKey: 'myRequests.times.today',
        time: timeStr,
        severity: 'high',
      };
  }
}

function getRequestIcon(type: RequestType) {
  switch (type) {
    case 'evacuation': return 'walk-outline';
    case 'help': return 'hand-left-outline';
    case 'relief': return 'heart-outline';
    case 'volunteer': return 'people-outline';
    case 'field_report': return 'camera-outline';
    default: return 'document-text-outline';
  }
}

function getRequestIconBg(type: RequestType) {
  switch (type) {
    case 'evacuation': return colors.sosBackground;
    case 'help': return '#FFF3E0';
    case 'relief': return '#E3F2FD';
    case 'volunteer': return '#E8F5E9';
    case 'field_report': return '#EDE7F6';
    default: return colors.backgroundGray;
  }
}

function getSeverityColor(severity: string) {
  switch (severity) {
    case 'critical': return '#D32F2F';
    case 'high': return '#FF5722';
    case 'medium': return '#FF9800';
    case 'low': return '#4CAF50';
    default: return colors.textLight;
  }
}

function getSyncBadgeLabel(status: import('../types').SyncStatus): string {
  switch (status) {
    case 'local_only': return 'Saved Offline';
    case 'syncing': return 'Uploading';
    case 'server_confirmed': return 'Submitted';
    case 'sync_failed': return 'Delivery Not Confirmed';
    default: return 'Saved';
  }
}

function getSyncBadgeBg(status: import('../types').SyncStatus): string {
  switch (status) {
    case 'local_only': return '#EEEEEE';
    case 'syncing': return '#E3F2FD';
    case 'server_confirmed': return '#E8F5E9';
    case 'sync_failed': return '#FFF3E0';
    default: return '#EEEEEE';
  }
}

function getSyncBadgeText(status: import('../types').SyncStatus): string {
  switch (status) {
    case 'local_only': return '#616161';
    case 'syncing': return '#1976D2';
    case 'server_confirmed': return '#2E7D32';
    case 'sync_failed': return '#E65100';
    default: return '#616161';
  }
}

export function MyRequestsScreen({ navigation }: MyRequestsScreenProps) {
  const { requests: localRequests } = useLocalRequests();
  const { t } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeFilter, setActiveFilter] = useState('all');

  const getItemTitle = (item: RequestItem): string => {
    if (item.titleKey) return t(item.titleKey, item.titleParams);
    return item.title ?? '';
  };

  const getItemDescription = (item: RequestItem): string => {
    if (item.descriptionKey) return t(item.descriptionKey, item.descriptionParams);
    return item.description ?? '';
  };

  const getItemDate = (item: RequestItem): string => {
    if (item.dateKey) return t(item.dateKey);
    return item.date ?? '';
  };

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 800);
    return () => clearTimeout(timer);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 1000);
  };

  const allItems: RequestItem[] = useMemo(() => {
    const localItems = localRequests.map(localRequestToItem);
    return [...localItems, ...MOCK_REQUESTS];
  }, [localRequests]);

  const filteredRequests = activeFilter === 'all'
    ? allItems
    : allItems.filter((r) => r.status === activeFilter);

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Ionicons name="arrow-back" size={24} color={colors.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>{t('myRequests.title')}</Text>
          <View style={{ width: 32 }} />
        </View>
        <LoadingState message={t('myRequests.loading')} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('myRequests.title')}</Text>
        <View style={{ width: 32 }} />
      </View>

      <View style={styles.statsBar}>
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{allItems.filter(r => r.status === 'pending').length}</Text>
          <Text style={[styles.statLabel, { color: colors.warning }]}>{t('myRequests.pending')}</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{allItems.filter(r => r.status === 'in_progress').length}</Text>
          <Text style={[styles.statLabel, { color: colors.info }]}>{t('myRequests.active')}</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{allItems.filter(r => r.status === 'resolved').length}</Text>
          <Text style={[styles.statLabel, { color: colors.success }]}>{t('myRequests.resolved')}</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{allItems.length}</Text>
          <Text style={[styles.statLabel, { color: colors.textSecondary }]}>{t('myRequests.total')}</Text>
        </View>
      </View>

      <View style={styles.filterBar}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterScroll}>
          {FILTERS.map((filter) => (
            <TouchableOpacity
              key={filter.key}
              style={[styles.filterChip, activeFilter === filter.key && styles.activeFilterChip]}
              onPress={() => setActiveFilter(filter.key)}
            >
              <Text style={[styles.filterText, activeFilter === filter.key && styles.activeFilterText]}>
                {t(filter.labelKey)}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {filteredRequests.length === 0 ? (
        <EmptyState
          icon="document-text-outline"
          title={t('myRequests.noRequests')}
          description={
            activeFilter === 'all'
              ? t('myRequests.noRequestsAll')
              : t('myRequests.noRequestsFilter', { filter: activeFilter.replace('_', ' ') })
          }
        />
      ) : (
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} colors={[colors.primary]} />
          }
        >
          {filteredRequests.map((request) => (
            <Card key={request.id} style={styles.requestCard}>
              <View style={styles.requestHeader}>
                <View style={[styles.requestIcon, { backgroundColor: getRequestIconBg(request.type) }]}>
                  <Ionicons name={getRequestIcon(request.type) as any} size={20} color={colors.primary} />
                </View>
                <View style={styles.requestInfo}>
                  <View style={styles.requestTitleRow}>
                    <Text style={styles.requestTitle} numberOfLines={1}>{getItemTitle(request)}</Text>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                      {request.syncStatus && (
                        <Text
                          style={[
                            styles.syncBadge,
                            { backgroundColor: getSyncBadgeBg(request.syncStatus), color: getSyncBadgeText(request.syncStatus) },
                          ]}
                        >
                          {getSyncBadgeLabel(request.syncStatus)}
                        </Text>
                      )}
                      <StatusBadge status={request.status} />
                    </View>
                  </View>
                  <Text style={styles.requestId}>{request.id}</Text>
                </View>
              </View>

              <Text style={styles.requestDescription} numberOfLines={2}>{getItemDescription(request)}</Text>

              <View style={styles.requestMeta}>
                <View style={styles.metaItem}>
                  <Ionicons name="location-outline" size={14} color={colors.textLight} />
                  <Text style={styles.metaText} numberOfLines={1}>{request.location}</Text>
                </View>
                <View style={styles.metaItem}>
                  <Ionicons name="time-outline" size={14} color={colors.textLight} />
                  <Text style={styles.metaText}>{getItemDate(request)} · {request.time}</Text>
                </View>
              </View>

              <View style={styles.requestFooter}>
                <View style={styles.severityIndicator}>
                  <View style={[styles.severityDot, { backgroundColor: getSeverityColor(request.severity) }]} />
                  <Text style={styles.severityLabel}>
                    {t('myRequests.priority', {
                      severity:
                        request.severity.charAt(0).toUpperCase() + request.severity.slice(1),
                    })}
                  </Text>
                </View>
                {request.responders !== undefined && request.responders > 0 && (
                  <View style={styles.respondersInfo}>
                    <Ionicons name="people-outline" size={14} color={colors.primary} />
                    <Text style={styles.respondersText}>
                      {request.responders === 1
                        ? t('myRequests.respondersOne')
                        : t('myRequests.responders', { count: request.responders })}
                    </Text>
                  </View>
                )}
              </View>
            </Card>
          ))}
          <View style={{ height: spacing.xxxl }} />
        </ScrollView>
      )}
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
    justifyContent: 'space-between',
    paddingHorizontal: spacing.base,
    paddingTop: spacing.xxl,
    paddingBottom: spacing.md,
    backgroundColor: colors.white,
  },
  backBtn: {
    padding: spacing.xs,
  },
  headerTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
  },
  statsBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.white,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.base,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
  },
  statLabel: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.medium,
    marginTop: 2,
  },
  statDivider: {
    width: 1,
    height: 30,
    backgroundColor: colors.borderLight,
  },
  filterBar: {
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
  },
  filterScroll: {
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.sm,
    gap: spacing.sm,
  },
  filterChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 9999,
    backgroundColor: colors.backgroundGray,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  activeFilterChip: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterText: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    fontWeight: typography.fontWeight.medium,
  },
  activeFilterText: {
    color: colors.white,
  },
  scrollContent: {
    padding: spacing.base,
  },
  syncBadge: {
    fontSize: 10,
    fontWeight: '600',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    overflow: 'hidden',
  },
  requestCard: {
    marginBottom: spacing.sm,
  },
  requestHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  requestIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  requestInfo: {
    flex: 1,
  },
  requestTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.sm,
  },
  requestTitle: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    flex: 1,
  },
  requestId: {
    fontSize: typography.fontSize.xs,
    color: colors.textLight,
    marginTop: 2,
  },
  requestDescription: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    lineHeight: 18,
    marginBottom: spacing.sm,
  },
  requestMeta: {
    gap: spacing.xs,
    marginBottom: spacing.sm,
    paddingBottom: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  metaText: {
    fontSize: typography.fontSize.xs,
    color: colors.textLight,
    flex: 1,
  },
  requestFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  severityIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  severityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  severityLabel: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
    fontWeight: typography.fontWeight.medium,
  },
  respondersInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  respondersText: {
    fontSize: typography.fontSize.xs,
    color: colors.primary,
    fontWeight: typography.fontWeight.medium,
  },
});
