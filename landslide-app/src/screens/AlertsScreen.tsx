import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AlertCard } from '../components';
import { LoadingState, EmptyState, ErrorState } from '../components/LoadingState';
import { colors } from '../theme/colors';
import { typography, spacing, borderRadius } from '../theme';
import { useLanguage, type TranslationKey } from '../i18n';

interface AlertsScreenProps {
  navigation: any;
}

type AlertSeverity = 'critical' | 'high' | 'medium' | 'low';

interface AlertItem {
  id: string;
  severity: AlertSeverity;
  titleKey: TranslationKey;
  descriptionKey: TranslationKey;
  locationKey: TranslationKey;
  timeKey: TranslationKey;
  read: boolean;
  category: string;
}

const MOCK_ALERTS: AlertItem[] = [
  {
    id: '1',
    severity: 'critical',
    titleKey: 'alerts.items.heavyRainTitle',
    descriptionKey: 'alerts.items.heavyRainDesc',
    locationKey: 'alerts.srinagar',
    timeKey: 'alerts.times.t10',
    read: false,
    category: 'weather',
  },
  {
    id: '2',
    severity: 'high',
    titleKey: 'alerts.items.landslideTitle',
    descriptionKey: 'alerts.items.landslideDesc',
    locationKey: 'alerts.baramulla',
    timeKey: 'alerts.times.t30',
    read: false,
    category: 'landslide',
  },
  {
    id: '3',
    severity: 'high',
    titleKey: 'alerts.items.rescueTitle',
    descriptionKey: 'alerts.items.rescueDesc',
    locationKey: 'alerts.anantnag',
    timeKey: 'alerts.times.t45',
    read: true,
    category: 'rescue',
  },
  {
    id: '4',
    severity: 'medium',
    titleKey: 'alerts.items.floodTitle',
    descriptionKey: 'alerts.items.floodDesc',
    locationKey: 'alerts.pulwama',
    timeKey: 'alerts.times.t1h',
    read: true,
    category: 'weather',
  },
  {
    id: '5',
    severity: 'medium',
    titleKey: 'alerts.items.roadTitle',
    descriptionKey: 'alerts.items.roadDesc',
    locationKey: 'alerts.baramullaSrinagar',
    timeKey: 'alerts.times.t2h',
    read: true,
    category: 'infrastructure',
  },
  {
    id: '6',
    severity: 'low',
    titleKey: 'alerts.items.weatherTitle',
    descriptionKey: 'alerts.items.weatherDesc',
    locationKey: 'alerts.jammu',
    timeKey: 'alerts.times.t3h',
    read: true,
    category: 'weather',
  },
  {
    id: '7',
    severity: 'low',
    titleKey: 'alerts.items.reliefTitle',
    descriptionKey: 'alerts.items.reliefDesc',
    locationKey: 'alerts.kupwara',
    timeKey: 'alerts.times.t5h',
    read: true,
    category: 'relief',
  },
];

type FilterType = 'all' | 'unread' | 'critical' | 'high' | 'medium' | 'low';

const FILTER_LABEL_KEYS: Record<FilterType, TranslationKey> = {
  all: 'alerts.filters.all',
  unread: 'alerts.filters.unread',
  critical: 'alerts.filters.critical',
  high: 'alerts.filters.high',
  medium: 'alerts.filters.medium',
  low: 'alerts.filters.low',
};

export function AlertsScreen({ navigation }: AlertsScreenProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');
  const { t } = useLanguage();

  useEffect(() => {
    const timer = setTimeout(() => {
      setAlerts(MOCK_ALERTS);
      setLoading(false);
    }, 800);
    return () => clearTimeout(timer);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => {
      setAlerts(MOCK_ALERTS);
      setRefreshing(false);
    }, 1000);
  };

  const handleRetry = () => {
    setLoading(true);
    setError(false);
    setTimeout(() => {
      setAlerts(MOCK_ALERTS);
      setLoading(false);
    }, 800);
  };

  const filteredAlerts = alerts.filter((alert) => {
    if (activeFilter === 'all') return true;
    if (activeFilter === 'unread') return !alert.read;
    return alert.severity === activeFilter;
  });

  const unreadCount = alerts.filter((a) => !a.read).length;

  const filters: { key: FilterType; label: string }[] = [
    { key: 'all', label: t('alerts.filters.all') },
    { key: 'unread', label: `${t('alerts.filters.unread')}${unreadCount > 0 ? ` (${unreadCount})` : ''}` },
    { key: 'critical', label: t('alerts.filters.critical') },
    { key: 'high', label: t('alerts.filters.high') },
    { key: 'medium', label: t('alerts.filters.medium') },
    { key: 'low', label: t('alerts.filters.low') },
  ];

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Ionicons name="arrow-back" size={24} color={colors.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>{t('alerts.title')}</Text>
          <View style={{ width: 32 }} />
        </View>
        <LoadingState message={t('alerts.loading')} />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Ionicons name="arrow-back" size={24} color={colors.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>{t('alerts.title')}</Text>
          <View style={{ width: 32 }} />
        </View>
        <ErrorState
          message={t('alerts.errorMessage')}
          onRetry={handleRetry}
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('alerts.title')}</Text>
        {unreadCount > 0 && (
          <View style={styles.unreadBadge}>
            <Text style={styles.unreadBadgeText}>{unreadCount}</Text>
          </View>
        )}
        <View style={{ flex: 1 }} />
      </View>

      <View style={styles.filterBar}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filterScroll}
        >
          {filters.map((filter) => (
            <TouchableOpacity
              key={filter.key}
              style={[styles.filterChip, activeFilter === filter.key && styles.activeFilterChip]}
              onPress={() => setActiveFilter(filter.key)}
            >
              <Text style={[styles.filterText, activeFilter === filter.key && styles.activeFilterText]}>
                {filter.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {filteredAlerts.length === 0 ? (
        <EmptyState
          icon="notifications-off-outline"
          title={t('alerts.noAlerts')}
          description={
            activeFilter === 'unread'
              ? t('alerts.noUnread')
              : t('alerts.noSeverity', {
                  severity: t(FILTER_LABEL_KEYS[activeFilter] as TranslationKey),
                })
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
          {filteredAlerts.map((alert) => (
            <TouchableOpacity
              key={alert.id}
              onPress={() => {
                setAlerts((prev) =>
                  prev.map((a) => (a.id === alert.id ? { ...a, read: true } : a))
                );
              }}
              activeOpacity={0.8}
            >
              <View style={!alert.read && styles.unreadWrapper}>
                <AlertCard
                  severity={alert.severity}
                  title={t(alert.titleKey)}
                  description={t(alert.descriptionKey)}
                  location={t(alert.locationKey)}
                  time={t(alert.timeKey)}
                />
                {!alert.read && <View style={styles.unreadDot} />}
              </View>
            </TouchableOpacity>
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
    paddingHorizontal: spacing.base,
    paddingTop: spacing.xxl,
    paddingBottom: spacing.md,
    backgroundColor: colors.white,
  },
  backBtn: {
    padding: spacing.xs,
    marginRight: spacing.sm,
  },
  headerTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
  },
  unreadBadge: {
    backgroundColor: colors.primary,
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 6,
    marginLeft: spacing.sm,
  },
  unreadBadgeText: {
    color: colors.white,
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.bold,
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
    paddingBottom: spacing.xxxl,
  },
  unreadWrapper: {
    position: 'relative',
  },
  unreadDot: {
    position: 'absolute',
    top: spacing.base + spacing.sm,
    right: spacing.base + spacing.sm,
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.white,
    borderWidth: 2,
    borderColor: colors.primary,
  },
});
