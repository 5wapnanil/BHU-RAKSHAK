import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  SafeAreaView,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { EmergencyButton } from '../components/EmergencyButton';
import { Card, AppButton } from '../components';
import { colors } from '../theme/colors';
import { typography, spacing, borderRadius } from '../theme';
import { useCurrentLocation } from '../hooks/useCurrentLocation';
import { useLocationShare } from '../hooks/useLocationShare';
import { useSOS } from '../hooks/useSOS';
import { useLanguage } from '../i18n';

interface EmergencyCenterScreenProps {
  navigation: any;
}

const EMERGENCY_ACTIONS = [
  { key: 'request_help', labelKey: 'emergencyCenter.requestHelp', icon: 'hand-left-outline', bgColor: '#FFF3E0', iconColor: '#FF9800', screen: 'RequestRelief' },
  { key: 'evacuation', labelKey: 'emergencyCenter.evacuation', icon: 'walk-outline', bgColor: '#FFF0ED', iconColor: colors.primary, screen: 'CallForEvacuation' },
  { key: 'request_relief', labelKey: 'emergencyCenter.requestRelief', icon: 'nutrition-outline', bgColor: '#E3F2FD', iconColor: '#2196F3', screen: 'RequestRelief' },
] as const;

export function EmergencyCenterScreen({ navigation }: EmergencyCenterScreenProps) {
  const [sosActivated, setSosActivated] = useState(false);
  const [buttonKey, setButtonKey] = useState(0);
  const { location, state: locationState, getLocation } = useCurrentLocation();
  const { shareState, shareLocation } = useLocationShare();
  const { activateSOS, state: sosState } = useSOS();
  const { t } = useLanguage();

  const handleSOSActivated = async () => {
    const handedOff = await activateSOS();
    if (handedOff) {
      setSosActivated(true);
    } else {
      setButtonKey((prev) => prev + 1);
    }
    return handedOff;
  };

  const handleCancelSOS = () => {
    Alert.alert(
      t('emergencyCenter.cancelSosTitle'),
      t('emergencyCenter.cancelSosMessage'),
      [
        { text: t('common.cancel'), style: 'cancel' },
        { text: t('emergencyCenter.confirm'), onPress: () => setSosActivated(false) },
      ]
    );
  };

  const handleActionPress = (screenName: string | null) => {
    if (screenName) {
      navigation.navigate(screenName);
    } else {
      Alert.alert(t('emergencyCenter.emergencyCall'), t('emergencyCenter.emergencyCallUnavailable'));
    }
  };

  const getLocationStatusText = () => {
    switch (locationState) {
      case 'locating':
        return t('emergencyCenter.gettingLocation');
      case 'requesting_permission':
        return t('emergencyCenter.requestingPermission');
      case 'success':
        if (location) {
          return t('emergencyCenter.locationReady', {
            coords: `${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}`,
          });
        }
        return t('emergencyCenter.locationReadyShort');
      case 'permission_denied':
        return t('emergencyCenter.locationDenied');
      case 'error':
        return t('emergencyCenter.locationUnavailable');
      default:
        return t('emergencyCenter.locationAvailable');
    }
  };

  const getLocationStatusColor = () => {
    if (locationState === 'success') return colors.success;
    if (locationState === 'permission_denied' || locationState === 'error') return colors.error;
    return colors.textSecondary;
  };

  if (sosActivated) {
    return (
      <SafeAreaView style={styles.container}>
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <View style={styles.header}>
            <TouchableOpacity onPress={handleCancelSOS} style={styles.cancelBtn}>
              <Text style={styles.cancelText}>{t('common.cancelSos')}</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.activatedSection}>
            <Ionicons name="alert-circle-outline" size={48} color={colors.error} />
            <Text style={styles.activatedTitle}>{t('emergencyCenter.sosActivated')}</Text>
            <Text style={styles.activatedSubtitle}>{t('emergencyCenter.sosActive')}</Text>
          </View>

          <Text style={styles.sectionTitle}>{t('emergencyCenter.emergencyActions')}</Text>
          <View style={styles.actionsGrid}>
            {EMERGENCY_ACTIONS.map((action) => (
              <TouchableOpacity
                key={action.key}
                style={[styles.actionCard, { backgroundColor: action.bgColor }]}
                onPress={() => navigation.navigate(action.screen)}
                activeOpacity={0.7}
              >
                <View style={[styles.actionIconWrap, { backgroundColor: action.iconColor + '18' }]}>
                  <Ionicons name={action.icon as any} size={28} color={action.iconColor} />
                </View>
                <Text style={styles.actionTitle}>{t(action.labelKey)}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity
            style={[
              styles.shareLocationBtn,
              (shareState === 'getting_location' || shareState === 'sharing') && styles.shareLocationBtnLoading,
            ]}
            onPress={shareLocation}
            disabled={shareState === 'getting_location' || shareState === 'sharing'}
          >
            {shareState === 'getting_location' || shareState === 'sharing' ? (
              <ActivityIndicator size={16} color={colors.textLight} />
            ) : (
              <Ionicons name="share-social-outline" size={18} color={colors.primary} />
            )}
            <Text style={[
              styles.shareLocationBtnText,
              (shareState === 'getting_location' || shareState === 'sharing') && styles.shareLocationBtnTextLoading,
            ]}>
              {shareState === 'getting_location' ? t('common.gettingLocation') : t('emergencyCenter.shareMyLocation')}
            </Text>
          </TouchableOpacity>

          <View style={styles.cancelSection}>
            <AppButton title={t('common.cancelSos')} variant="outline" onPress={handleCancelSOS} />
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.title}>{t('emergencyCenter.title')}</Text>
          <Text style={styles.subtitle}>{t('emergencyCenter.subtitle')}</Text>
        </View>

        <Card style={styles.locationCard}>
          <View style={styles.locationHeader}>
            <Ionicons name="location-outline" size={20} color={colors.primary} />
            <Text style={styles.locationLabel}>{t('emergencyCenter.locationStatus')}</Text>
          </View>
          <View style={styles.locationStatus}>
            <TouchableOpacity
              style={[styles.refreshBtn, locationState === 'locating' && styles.refreshBtnLoading]}
              onPress={getLocation}
              disabled={locationState === 'locating' || locationState === 'requesting_permission'}
            >
              <Ionicons
                name="refresh"
                size={18}
                color={locationState === 'locating' ? colors.textLight : colors.primary}
              />
            </TouchableOpacity>
            <Text style={[styles.locationStatusText, { color: getLocationStatusColor() }]}>
              {getLocationStatusText()}
            </Text>
          </View>
        </Card>

        <TouchableOpacity
          style={[
            styles.shareLocationBtn,
            (shareState === 'getting_location' || shareState === 'sharing') && styles.shareLocationBtnLoading,
          ]}
          onPress={shareLocation}
          disabled={shareState === 'getting_location' || shareState === 'sharing'}
        >
          {shareState === 'getting_location' || shareState === 'sharing' ? (
            <ActivityIndicator size={16} color={colors.textLight} />
          ) : (
            <Ionicons name="share-social-outline" size={18} color={colors.primary} />
          )}
          <Text style={[
            styles.shareLocationBtnText,
            (shareState === 'getting_location' || shareState === 'sharing') && styles.shareLocationBtnTextLoading,
          ]}>
            {shareState === 'getting_location' ? t('common.gettingLocation') : t('emergencyCenter.shareMyLocation')}
          </Text>
        </TouchableOpacity>

        <View style={styles.sosSection}>
          <EmergencyButton
            key={buttonKey}
            onSOSActivated={handleSOSActivated}
            size={140}
            disabled={sosState !== 'idle'}
          />
          <Text style={styles.sosHint}>{t('emergencyCenter.sosHint')}</Text>
        </View>

        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>{t('emergencyCenter.howItWorks')}</Text>
          <Text style={styles.infoText}>
            {t('emergencyCenter.howItWorksText')}
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.backgroundLight,
  },
  scrollContent: {
    paddingBottom: spacing.xxxl,
    paddingHorizontal: spacing.base,
  },
  header: {
    alignItems: 'center',
    paddingTop: spacing.xl,
    paddingBottom: spacing.lg,
  },
  title: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  subtitle: {
    fontSize: typography.fontSize.md,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  cancelBtn: {
    position: 'absolute',
    top: spacing.md,
    right: spacing.base,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    backgroundColor: colors.error + '20',
    borderRadius: borderRadius.round,
  },
  cancelText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.error,
  },
  locationCard: {
    marginBottom: spacing.xl,
  },
  locationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  locationLabel: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  locationStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  refreshBtn: {
    padding: spacing.xs,
    backgroundColor: colors.sosBackground,
    borderRadius: borderRadius.round,
  },
  refreshBtnLoading: {
    backgroundColor: colors.backgroundGray,
  },
  locationStatusText: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.medium,
    flex: 1,
  },
  shareLocationBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.base,
    borderRadius: borderRadius.round,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.primary + '30',
    marginBottom: spacing.xl,
  },
  shareLocationBtnLoading: {
    backgroundColor: colors.backgroundGray,
    borderColor: colors.border,
  },
  shareLocationBtnText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    color: colors.primary,
  },
  shareLocationBtnTextLoading: {
    color: colors.textLight,
  },
  sosSection: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
    marginBottom: spacing.xl,
  },
  sosHint: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginTop: spacing.md,
    textAlign: 'center',
    paddingHorizontal: spacing.md,
  },
  infoCard: {
    backgroundColor: colors.infoLight,
    borderLeftWidth: 4,
    borderLeftColor: colors.info,
  },
  infoTitle: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  infoText: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    lineHeight: 20,
  },
  activatedSection: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
    marginBottom: spacing.xl,
  },
  activatedTitle: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.error,
    marginTop: spacing.md,
    marginBottom: spacing.xs,
  },
  activatedSubtitle: {
    fontSize: typography.fontSize.md,
    color: colors.textSecondary,
  },
  sectionTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    marginBottom: spacing.md,
    marginTop: spacing.sm,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.xl,
  },
  actionCard: {
    width: '48%',
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    minHeight: 100,
    justifyContent: 'center',
    alignItems: 'center',
  },
  actionIconWrap: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  actionTitle: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    textAlign: 'center',
    lineHeight: 18,
  },
  cancelSection: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
  },
});