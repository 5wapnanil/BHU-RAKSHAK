import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Linking,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card, AppButton } from '../components';
import { LoadingState, EmptyState, ErrorState } from '../components/LoadingState';
import { colors } from '../theme/colors';
import { typography, spacing, borderRadius } from '../theme';
import { useCurrentLocation } from '../hooks/useCurrentLocation';
import { getShelters, type Shelter } from '../services/api/operationsApi';
import { useLanguage, type TranslationKey } from '../i18n';
import type { LocationCoords } from '../services/location';

interface NearbySheltersScreenProps {
  navigation: any;
}

interface ShelterWithDistance extends Shelter {
  distanceKm: number | null;
  hasCoords: boolean;
}

function haversineDistance(a: LocationCoords, b: LocationCoords): number {
  const R = 6371;
  const dLat = ((b.latitude - a.latitude) * Math.PI) / 180;
  const dLon = ((b.longitude - a.longitude) * Math.PI) / 180;
  const x =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((a.latitude * Math.PI) / 180) *
      Math.cos((b.latitude * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  return R * 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1 - x));
}

function parseCoordinates(shelter: Shelter): LocationCoords | null {
  if (shelter.location) {
    try {
      const parsed = JSON.parse(shelter.location);
      if (typeof parsed.latitude === 'number' && typeof parsed.longitude === 'number') {
        return { latitude: parsed.latitude, longitude: parsed.longitude };
      }
    } catch {
      const match = shelter.location.match(
        /(-?\d+\.?\d*)\s*[,]\s*(-?\d+\.?\d*)/,
      );
      if (match) {
        const lat = parseFloat(match[1]);
        const lon = parseFloat(match[2]);
        if (!isNaN(lat) && !isNaN(lon)) {
          return { latitude: lat, longitude: lon };
        }
      }
    }
  }
  return null;
}

function formatDistance(km: number | null): string {
  if (km === null) return '';
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(1)} km`;
}

function getStatusColor(status: string) {
  switch (status?.toUpperCase()) {
    case 'OPEN':
      return colors.success;
    case 'FULL':
      return colors.error;
    case 'CLOSED':
      return colors.textLight;
    default:
      return colors.textLight;
  }
}

function getStatusBg(status: string) {
  switch (status?.toUpperCase()) {
    case 'OPEN':
      return colors.successLight;
    case 'FULL':
      return colors.errorLight;
    case 'CLOSED':
      return colors.backgroundGray;
    default:
      return colors.backgroundGray;
  }
}

function getStatusLabelKey(status: string): TranslationKey {
  switch (status?.toUpperCase()) {
    case 'OPEN':
      return 'shelters.status.open';
    case 'FULL':
      return 'shelters.status.full';
    case 'CLOSED':
      return 'shelters.status.closed';
    default:
      return 'common.unknown';
  }
}

function formatFacilities(facilities: Record<string, unknown> | null): string[] {
  if (!facilities) return [];
  if (typeof facilities === 'object' && !Array.isArray(facilities)) {
    return Object.keys(facilities).filter((k) => facilities[k]);
  }
  if (Array.isArray(facilities)) {
    return facilities.filter(Boolean).map(String);
  }
  return [];
}

function openMaps(shelter: Shelter, t: (key: TranslationKey) => string) {
  const coords = parseCoordinates(shelter);
  const query = coords
    ? `${coords.latitude},${coords.longitude}`
    : shelter.address || shelter.name;

  const url = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(query)}`;
  Linking.openURL(url).catch(() => {
    Alert.alert(t('shelters.mapsUnavailable'), t('shelters.mapsUnavailableMessage'));
  });
}

export function NearbySheltersScreen({ navigation }: NearbySheltersScreenProps) {
  const { location, state: locationState, getLocation } = useCurrentLocation();
  const { t } = useLanguage();
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableOnly, setAvailableOnly] = useState(false);

  useEffect(() => {
    getLocation();
  }, []);

  const fetchShelters = useCallback(async () => {
    try {
      const result = await getShelters(200);
      if (result.success && result.data) {
        setShelters(result.data);
        setError(null);
      } else {
        setError(result.error?.message || t('shelters.unableToLoadMessage'));
      }
    } catch {
      setError(t('shelters.unableToLoadMessage'));
    }
  }, [t]);

  useEffect(() => {
    let cancelled = false;
    fetchShelters().finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, [fetchShelters]);

  const sheltersWithDistance = useMemo<ShelterWithDistance[]>(() => {
    return shelters.map((s) => {
      const coords = parseCoordinates(s);
      const distanceKm =
        location && coords ? haversineDistance(location, coords) : null;
      return { ...s, distanceKm, hasCoords: coords !== null };
    }).sort((a, b) => {
      if (a.distanceKm === null && b.distanceKm === null) return 0;
      if (a.distanceKm === null) return 1;
      if (b.distanceKm === null) return -1;
      return a.distanceKm - b.distanceKm;
    });
  }, [shelters, location]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    if (locationState !== 'success') {
      getLocation();
    }
    await fetchShelters();
    setRefreshing(false);
  }, [locationState, getLocation, fetchShelters]);

  const filteredShelters = useMemo(() => {
    if (!availableOnly) return sheltersWithDistance;
    return sheltersWithDistance.filter(
      (s) => s.status?.toUpperCase() === 'OPEN',
    );
  }, [sheltersWithDistance, availableOnly]);

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Ionicons name="arrow-back" size={22} color={colors.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>{t('shelters.title')}</Text>
          <View style={{ width: 40 }} />
        </View>
        <LoadingState
          message={
            locationState === 'locating' || locationState === 'requesting_permission'
              ? t('shelters.gettingLocation')
              : t('shelters.findingShelters')
          }
        />
      </SafeAreaView>
    );
  }

  if (error && shelters.length === 0) {
    return (
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Ionicons name="arrow-back" size={22} color={colors.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>{t('shelters.title')}</Text>
          <View style={{ width: 40 }} />
        </View>
        <ErrorState
          title={t('shelters.unableToLoad')}
          message={error}
          onRetry={() => {
            setLoading(true);
            fetchShelters().finally(() => setLoading(false));
          }}
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={22} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('shelters.title')}</Text>
        <View style={{ width: 40 }} />
      </View>

      <Text style={styles.subtitle}>
        {t('shelters.subtitle')}
      </Text>

      <View style={styles.filterRow}>
        <TouchableOpacity
          style={[styles.filterChip, availableOnly && styles.filterChipActive]}
          onPress={() => setAvailableOnly(!availableOnly)}
          activeOpacity={0.7}
        >
          <Ionicons
            name={availableOnly ? 'checkmark-circle' : 'ellipse-outline'}
            size={16}
            color={availableOnly ? colors.white : colors.textSecondary}
          />
          <Text style={[styles.filterText, availableOnly && styles.filterTextActive]}>
            {t('shelters.availableOnly')}
          </Text>
        </TouchableOpacity>
        {locationState === 'success' && location && (
          <View style={styles.locationBadge}>
            <Ionicons name="locate" size={14} color={colors.primary} />
            <Text style={styles.locationBadgeText}>{t('shelters.gpsActive')}</Text>
          </View>
        )}
      </View>

      {filteredShelters.length === 0 ? (
        <ScrollView
          contentContainerStyle={styles.emptyContainer}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} colors={[colors.primary]} />
          }
        >
          <EmptyState
            icon="home-outline"
            title={t('shelters.noSheltersTitle')}
            description={
              availableOnly
                ? t('shelters.noSheltersAvailableDesc')
                : t('shelters.noSheltersDesc')
            }
          />
          <AppButton title={t('common.refresh')} variant="outline" onPress={handleRefresh} style={styles.refreshBtn} />
        </ScrollView>
      ) : (
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} colors={[colors.primary]} />
          }
        >
          <Text style={styles.countText}>
            {filteredShelters.length === 1
              ? t('shelters.foundCountOne')
              : t('shelters.foundCount', { count: filteredShelters.length })}
          </Text>

          {filteredShelters.map((shelter) => {
            const occupancy = shelter.current_occupancy;
            const capacity = shelter.capacity;
            const hasValidOccupancy =
              typeof occupancy === 'number' &&
              typeof capacity === 'number' &&
              capacity > 0;
            const occupancyPercent = hasValidOccupancy
              ? Math.min(Math.round((occupancy / capacity) * 100), 100)
              : null;
            const available = hasValidOccupancy ? capacity - occupancy : null;
            const facilities = formatFacilities(shelter.facilities);
            const statusColor = getStatusColor(shelter.status);
            const distanceText = formatDistance(shelter.distanceKm);
            const distanceLabel = distanceText
              ? t('shelters.distanceAway', { value: distanceText })
              : '';

            return (
              <Card key={shelter.id} style={styles.shelterCard}>
                <View style={styles.shelterHeader}>
                  <View style={[styles.shelterIcon, { backgroundColor: statusColor + '18' }]}>
                    <Ionicons name="home" size={20} color={statusColor} />
                  </View>
                  <View style={styles.shelterInfo}>
                    <Text style={styles.shelterName}>{shelter.name}</Text>
                    {distanceLabel ? (
                      <Text style={styles.shelterDistance}>{distanceLabel}</Text>
                    ) : null}
                  </View>
                  <View style={[styles.statusBadge, { backgroundColor: getStatusBg(shelter.status) }]}>
                    <Text style={[styles.statusText, { color: statusColor }]}>
                      {t(getStatusLabelKey(shelter.status))}
                    </Text>
                  </View>
                </View>

                {shelter.address ? (
                  <Text style={styles.shelterAddress}>{shelter.address}</Text>
                ) : null}

                {hasValidOccupancy && (
                  <View style={styles.occupancySection}>
                    <View style={styles.occupancyBar}>
                      <View
                        style={[
                          styles.occupancyFill,
                          {
                            width: `${occupancyPercent!}%`,
                            backgroundColor: statusColor,
                          },
                        ]}
                      />
                    </View>
                    <View style={styles.occupancyRow}>
                      <Text style={styles.occupancyText}>
                        {occupancy} / {capacity} {t('shelters.occupied')}
                      </Text>
                      {available !== null && available > 0 && (
                        <Text style={styles.availableText}>
                          {available === 1
                            ? t('shelters.spaceAvailable')
                            : t('shelters.spacesAvailable', { count: available })}
                        </Text>
                      )}
                    </View>
                  </View>
                )}

                {facilities.length > 0 && (
                  <View style={styles.facilitiesRow}>
                    {facilities.slice(0, 5).map((f, idx) => (
                      <View key={idx} style={styles.facilityChip}>
                        <Text style={styles.facilityText}>{f}</Text>
                      </View>
                    ))}
                  </View>
                )}

                <View style={styles.shelterActions}>
                  <TouchableOpacity
                    style={styles.directionsBtn}
                    onPress={() => openMaps(shelter, t)}
                    activeOpacity={0.7}
                  >
                    <Ionicons name="navigate-outline" size={16} color={colors.primary} />
                    <Text style={styles.directionsText}>{t('shelters.getDirections')}</Text>
                  </TouchableOpacity>

                  {shelter.contact_phone ? (
                    <TouchableOpacity
                      style={styles.callBtn}
                      onPress={() => Linking.openURL(`tel:${shelter.contact_phone}`)}
                      activeOpacity={0.7}
                    >
                      <Ionicons name="call-outline" size={16} color={colors.primary} />
                      <Text style={styles.callText}>{t('shelters.call')}</Text>
                    </TouchableOpacity>
                  ) : null}
                </View>
              </Card>
            );
          })}

          <View style={{ height: spacing.xxxl }} />
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.backgroundLight,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.base,
    paddingTop: spacing.sm,
    paddingBottom: spacing.md,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.white,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  headerTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
  },
  subtitle: {
    fontSize: typography.fontSize.md,
    color: colors.textSecondary,
    marginHorizontal: spacing.base,
    marginBottom: spacing.md,
    lineHeight: 22,
  },
  filterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: spacing.base,
    marginBottom: spacing.md,
    gap: spacing.sm,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.round,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
  },
  filterChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterText: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    fontWeight: typography.fontWeight.medium,
  },
  filterTextActive: {
    color: colors.white,
  },
  locationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    backgroundColor: colors.primaryLight + '20',
    borderRadius: borderRadius.round,
  },
  locationBadgeText: {
    fontSize: typography.fontSize.xs,
    color: colors.primary,
    fontWeight: typography.fontWeight.medium,
  },
  listContent: {
    paddingHorizontal: spacing.base,
  },
  countText: {
    fontSize: typography.fontSize.sm,
    color: colors.textLight,
    marginBottom: spacing.sm,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: spacing.base,
  },
  refreshBtn: {
    marginTop: spacing.md,
    alignSelf: 'center',
  },
  shelterCard: {
    marginBottom: spacing.sm,
  },
  shelterHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  shelterIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  shelterInfo: {
    flex: 1,
  },
  shelterName: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  shelterDistance: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xxs,
    borderRadius: borderRadius.round,
  },
  statusText: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.semiBold,
  },
  shelterAddress: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  occupancySection: {
    marginBottom: spacing.sm,
  },
  occupancyBar: {
    height: 4,
    backgroundColor: colors.backgroundGray,
    borderRadius: 2,
    overflow: 'hidden',
    marginBottom: spacing.xs,
  },
  occupancyFill: {
    height: '100%',
    borderRadius: 2,
  },
  occupancyRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  occupancyText: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
  },
  availableText: {
    fontSize: typography.fontSize.xs,
    color: colors.success,
    fontWeight: typography.fontWeight.medium,
  },
  facilitiesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
    marginBottom: spacing.sm,
  },
  facilityChip: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xxs,
    backgroundColor: colors.backgroundGray,
    borderRadius: borderRadius.round,
  },
  facilityText: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
  },
  shelterActions: {
    flexDirection: 'row',
    gap: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.borderLight,
    paddingTop: spacing.sm,
  },
  directionsBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  directionsText: {
    fontSize: typography.fontSize.sm,
    color: colors.primary,
    fontWeight: typography.fontWeight.medium,
  },
  callBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  callText: {
    fontSize: typography.fontSize.sm,
    color: colors.primary,
    fontWeight: typography.fontWeight.medium,
  },
});
