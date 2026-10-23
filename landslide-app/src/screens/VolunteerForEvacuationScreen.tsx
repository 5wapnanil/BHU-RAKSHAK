import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppButton, Card, InputField } from '../components';
import { colors } from '../theme/colors';
import { typography, spacing, borderRadius } from '../theme';
import { useLocalRequests } from '../hooks/useLocalRequests';
import { useCurrentLocation } from '../hooks/useCurrentLocation';
import { useLanguage, type TranslationKey } from '../i18n';
import {
  validateEvacuationVolunteerForm,
  firstEvacuationVolunteerError,
} from '../services/volunteers/workflow';

interface VolunteerForEvacuationScreenProps {
  navigation: any;
}

const CAPABILITIES = [
  { key: 'firstAid', labelKey: 'volunteer.capabilities.firstAid', icon: 'medkit-outline' },
  { key: 'driving', labelKey: 'volunteer.capabilities.driving', icon: 'car-outline' },
  { key: 'search', labelKey: 'volunteer.capabilities.search', icon: 'search-outline' },
  { key: 'counseling', labelKey: 'volunteer.capabilities.counseling', icon: 'heart-outline' },
  { key: 'translation', labelKey: 'volunteer.capabilities.translation', icon: 'language-outline' },
  { key: 'heavyLifting', labelKey: 'volunteer.capabilities.heavyLifting', icon: 'barbell-outline' },
] as const;

const AVAILABILITY_OPTIONS = [
  { value: 'Immediately', labelKey: 'common.immediately' },
  { value: 'Next 2 hours', labelKey: 'common.next2Hours' },
  { value: 'Next 6 hours', labelKey: 'common.next6Hours' },
  { value: 'Tomorrow', labelKey: 'common.tomorrow' },
] as const;

export function VolunteerForEvacuationScreen({ navigation }: VolunteerForEvacuationScreenProps) {
  const { addEvacuationVolunteer, syncToBackend } = useLocalRequests();
  const { location, state: locationState, error: locationError, address, getLocation } = useCurrentLocation();
  const { t } = useLanguage();

  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [currentLocation, setCurrentLocation] = useState('');
  const [hasTransport, setHasTransport] = useState<boolean | null>(null);
  const [capacity, setCapacity] = useState('');
  const [selectedCapabilities, setSelectedCapabilities] = useState<string[]>([]);
  const [availability, setAvailability] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (locationState === 'success' && address) {
      setCurrentLocation(address);
    }
  }, [locationState, address]);

  const toggleCapability = (key: string) => {
    setSelectedCapabilities((prev) =>
      prev.includes(key) ? prev.filter((c) => c !== key) : [...prev, key]
    );
  };

  const handleUseCurrentLocation = () => {
    getLocation();
  };

  const getLocationDisplayText = () => {
    if (locationState === 'locating') return t('emergencyCenter.gettingLocation');
    if (locationState === 'requesting_permission') return t('emergencyCenter.requestingPermission');
    if (locationState === 'success') {
      if (address) return t('volunteer.locationDetected');
      if (location) return t('volunteer.locationDetectedNoAddress');
      return t('volunteer.locationDetected');
    }
    if (locationState === 'permission_denied') return t('volunteer.locationPermissionNeeded');
    if (locationState === 'error') return locationError || t('volunteer.locationError');
    return null;
  };

  const handleSubmit = async () => {
    if (submitting) return;

    const errors = validateEvacuationVolunteerForm({
      name,
      phone,
      currentLocation,
      hasTransport,
      capacity,
      capabilities: selectedCapabilities,
      availability,
    });

    const firstError = firstEvacuationVolunteerError(errors);
    if (firstError) {
      const validationKeyMap: Record<string, TranslationKey> = {
        'Name is required.': 'validation.volunteerNameRequired',
        'Phone number is required.': 'validation.volunteerPhoneRequired',
        'Current location is required.': 'validation.volunteerLocationRequired',
        'Please indicate whether you have a vehicle.': 'validation.hasTransportRequired',
        'Transport capacity is required.': 'validation.capacityRequired',
        'Please select at least one capability.': 'validation.capabilitiesRequired',
        'Please select your availability.': 'validation.availabilityRequired',
      };
      const mapped = validationKeyMap[firstError];
      Alert.alert(t('common.required'), mapped ? t(mapped) : firstError);
      return;
    }

    setSubmitting(true);
    
    const request = addEvacuationVolunteer({
      name,
      phone,
      currentLocation,
      hasTransport,
      capacity,
      capabilities: selectedCapabilities,
      availability,
      gpsCoords: location || undefined,
    });

    const syncResult = await syncToBackend(request);
    
    setSubmitting(false);
    
    const backendMessage = syncResult.serverConfirmed
      ? t('volunteer.serverConfirmed')
      : t('volunteer.savedLocally');
    
    Alert.alert(
      t('volunteer.registeredTitle'),
      t('volunteer.registeredEvacuationMessage', { backendMessage }),
      [{ text: t('common.ok'), onPress: () => navigation.goBack() }]
    );
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Ionicons name="arrow-back" size={24} color={colors.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>{t('volunteer.evacuationTitle')}</Text>
          <View style={{ width: 32 }} />
        </View>

        <Text style={styles.screenSubtitle}>
          {t('volunteer.evacuationSubtitle')}
        </Text>

        <Card style={styles.infoCard}>
          <Ionicons name="people-outline" size={36} color={colors.primary} />
          <Text style={styles.infoTitle}>{t('volunteer.evacuationInfoTitle')}</Text>
          <Text style={styles.infoText}>
            {t('volunteer.evacuationInfoText')}
          </Text>
        </Card>

        <Card style={styles.statsCard}>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>128</Text>
            <Text style={styles.statLabel}>{t('volunteer.active')}</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>45</Text>
            <Text style={styles.statLabel}>{t('volunteer.missions')}</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>312</Text>
            <Text style={styles.statLabel}>{t('volunteer.helped')}</Text>
          </View>
        </Card>

        <View style={styles.formSection}>
          <Text style={styles.sectionTitle}>{t('volunteer.yourInformation')}</Text>

          <InputField
            label={t('volunteer.fullName')}
            placeholder={t('volunteer.fullNamePlaceholder')}
            value={name}
            onChangeText={setName}
            icon="person-outline"
          />

          <InputField
            label={t('volunteer.phoneNumber')}
            placeholder={t('volunteer.phoneNumberPlaceholder')}
            value={phone}
            onChangeText={setPhone}
            keyboardType="phone-pad"
            icon="call-outline"
          />

          <View style={styles.locationCard}>
            <View style={styles.locationHeader}>
              <Ionicons name="location" size={18} color={colors.primary} />
              <Text style={styles.locationLabel}>{t('volunteer.currentLocation')}</Text>
            </View>
            <InputField
              placeholder={t('volunteer.locationPlaceholder')}
              value={currentLocation}
              onChangeText={setCurrentLocation}
              icon="location-outline"
            />
            
            <TouchableOpacity
              style={[
                styles.gpsButton,
                locationState === 'locating' && styles.gpsButtonLoading,
              ]}
              onPress={handleUseCurrentLocation}
              disabled={locationState === 'locating' || locationState === 'requesting_permission'}
            >
              <Ionicons
                name="navigate"
                size={16}
                color={locationState === 'locating' ? colors.textLight : colors.primary}
              />
              <Text style={[
                styles.gpsButtonText,
                (locationState === 'locating' || locationState === 'requesting_permission') && styles.gpsButtonTextLoading,
              ]}>
                {getLocationDisplayText() || t('volunteer.useCurrentLocation')}
              </Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.fieldLabel}>{t('volunteer.haveVehicle')}</Text>
          <View style={styles.radioRow}>
            <TouchableOpacity
              style={[styles.radioOption, hasTransport === true && styles.radioActive]}
              onPress={() => setHasTransport(true)}
            >
              <View style={[styles.radioDot, hasTransport === true && styles.radioDotActive]} />
              <Text style={[styles.radioLabel, hasTransport === true && styles.radioLabelActive]}>
                {t('common.yes')}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.radioOption, hasTransport === false && styles.radioActive]}
              onPress={() => setHasTransport(false)}
            >
              <View style={[styles.radioDot, hasTransport === false && styles.radioDotActive]} />
              <Text style={[styles.radioLabel, hasTransport === false && styles.radioLabelActive]}>
                {t('common.no')}
              </Text>
            </TouchableOpacity>
          </View>

          <InputField
            label={t('volunteer.transportCapacity')}
            placeholder={t('volunteer.transportCapacityPlaceholder')}
            value={capacity}
            onChangeText={setCapacity}
            keyboardType="numeric"
            icon="people-outline"
          />

          <Text style={styles.fieldLabel}>{t('volunteer.yourCapabilities')}</Text>
          <View style={styles.chipContainer}>
            {CAPABILITIES.map((cap) => {
              const isSelected = selectedCapabilities.includes(cap.key);
              return (
                <TouchableOpacity
                  key={cap.key}
                  style={[styles.chip, isSelected && styles.chipActive]}
                  onPress={() => toggleCapability(cap.key)}
                >
                  <Ionicons
                    name={cap.icon as any}
                    size={16}
                    color={isSelected ? colors.white : colors.primary}
                  />
                  <Text style={[styles.chipText, isSelected && styles.chipTextActive]}>
                    {t(cap.labelKey)}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <Text style={styles.fieldLabel}>{t('volunteer.availability')}</Text>
          <View style={styles.chipContainer}>
            {AVAILABILITY_OPTIONS.map((option) => (
              <TouchableOpacity
                key={option.value}
                style={[styles.chip, availability === option.value && styles.chipActive]}
                onPress={() => setAvailability(option.value)}
              >
                <Text style={[styles.chipText, availability === option.value && styles.chipTextActive]}>
                  {t(option.labelKey)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <AppButton
            title={submitting ? t('volunteer.registering') : t('volunteer.registerEvacuation')}
            onPress={handleSubmit}
            loading={submitting}
            style={styles.submitBtn}
          />

          <AppButton
            title={t('volunteer.cancel')}
            variant="outline"
            onPress={() => navigation.goBack()}
            style={styles.cancelBtn}
          />
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.backgroundLight,
  },
  scrollContent: {
    paddingBottom: spacing.xxxl,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.base,
    paddingTop: spacing.xl,
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
  screenSubtitle: {
    fontSize: typography.fontSize.md,
    color: colors.textSecondary,
    marginHorizontal: spacing.base,
    marginTop: spacing.sm,
    marginBottom: spacing.base,
    lineHeight: 22,
  },
  infoCard: {
    marginHorizontal: spacing.base,
    alignItems: 'center',
    paddingVertical: spacing.xl,
    gap: spacing.sm,
  },
  infoTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
  },
  infoText: {
    fontSize: typography.fontSize.md,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
  statsCard: {
    marginHorizontal: spacing.base,
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.lg,
    marginTop: spacing.base,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: typography.fontSize.xxl,
    fontWeight: typography.fontWeight.bold,
    color: colors.primary,
  },
  statLabel: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
    marginTop: spacing.xxs,
  },
  statDivider: {
    width: 1,
    height: 40,
    backgroundColor: colors.border,
  },
  formSection: {
    paddingHorizontal: spacing.base,
    marginTop: spacing.base,
  },
  sectionTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    marginBottom: spacing.md,
  },
  locationCard: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  locationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  locationLabel: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  gpsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.base,
    borderRadius: borderRadius.round,
    backgroundColor: colors.sosBackground,
    marginTop: spacing.sm,
    borderWidth: 1,
    borderColor: colors.primary + '30',
  },
  gpsButtonLoading: {
    backgroundColor: colors.backgroundGray,
    borderColor: colors.border,
  },
  gpsButtonText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    color: colors.primary,
  },
  gpsButtonTextLoading: {
    color: colors.textLight,
  },
  fieldLabel: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    marginBottom: spacing.sm,
    marginTop: spacing.sm,
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.round,
    borderWidth: 1.5,
    borderColor: colors.primary,
    backgroundColor: colors.white,
  },
  chipActive: {
    backgroundColor: colors.primary,
  },
  chipText: {
    fontSize: typography.fontSize.sm,
    color: colors.primary,
    fontWeight: typography.fontWeight.medium,
  },
  chipTextActive: {
    color: colors.white,
  },
  radioRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  radioOption: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.white,
    minWidth: 100,
  },
  radioActive: {
    borderColor: colors.primary,
    backgroundColor: colors.sosBackground,
  },
  radioDot: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    borderColor: colors.border,
  },
  radioDotActive: {
    borderColor: colors.primary,
    backgroundColor: colors.primary,
  },
  radioLabel: {
    fontSize: typography.fontSize.md,
    color: colors.textSecondary,
    fontWeight: typography.fontWeight.medium,
  },
  radioLabelActive: {
    color: colors.primary,
  },
  submitBtn: {
    marginTop: spacing.lg,
  },
  cancelBtn: {
    marginTop: spacing.sm,
  },
});