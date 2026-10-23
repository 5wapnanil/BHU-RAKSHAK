import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Linking,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { EmergencyButton, AppButton, Card, InputField } from '../components';
import { colors } from '../theme/colors';
import { typography, spacing, borderRadius } from '../theme';
import { EMERGENCY_TYPES } from '../constants';
import { useLocalRequests } from '../hooks/useLocalRequests';
import { useCurrentLocation } from '../hooks/useCurrentLocation';
import { useSOS } from '../hooks/useSOS';
import { useLocationShare } from '../hooks/useLocationShare';
import {
  validateEvacuationForm,
  firstEvacuationError,
} from '../services/evacuation/workflow';
import { useLanguage, type TranslationKey } from '../i18n';

interface CallForEvacuationScreenProps {
  navigation: any;
}

const EMERGENCY_TYPE_LABEL_KEYS: Record<string, TranslationKey> = {
  fire: 'callForEvacuation.emergencyTypes.fire',
  earthquake: 'callForEvacuation.emergencyTypes.earthquake',
  flood: 'callForEvacuation.emergencyTypes.flood',
  landslide: 'callForEvacuation.emergencyTypes.landslide',
  cyclone: 'callForEvacuation.emergencyTypes.cyclone',
  other: 'callForEvacuation.emergencyTypes.other',
};

export function CallForEvacuationScreen({ navigation }: CallForEvacuationScreenProps) {
  const { addEvacuationRequest, syncToBackend } = useLocalRequests();
  const { location, state: locationState, error: locationError, address, getLocation } = useCurrentLocation();
  const { activateSOS, state: sosState } = useSOS();
  const { shareState, shareLocation } = useLocationShare();
  const { t } = useLanguage();

  const [locationText, setLocationText] = useState('');
  const [numberOfPeople, setNumberOfPeople] = useState('');
  const [selectedEmergency, setSelectedEmergency] = useState('');
  const [hasVulnerable, setHasVulnerable] = useState<boolean | null>(null);
  const [contactName, setContactName] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [additionalInfo, setAdditionalInfo] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (locationState === 'success' && address) {
      setLocationText(address);
    }
  }, [locationState, address]);

  const handleSOS = () => {
    return activateSOS();
  };

  const handleUseCurrentLocation = () => {
    getLocation();
  };

  const getLocationDisplayText = () => {
    if (locationState === 'locating') return t('emergencyCenter.gettingLocation');
    if (locationState === 'requesting_permission') return t('emergencyCenter.requestingPermission');
    if (locationState === 'success') {
      if (address) return t('callForEvacuation.locationDetected');
      if (location) return t('callForEvacuation.locationDetectedNoAddress');
      return t('callForEvacuation.locationDetected');
    }
    if (locationState === 'permission_denied') return t('callForEvacuation.locationPermissionNeeded');
    if (locationState === 'error') return locationError || t('callForEvacuation.locationError');
    return null;
  };

  const handleSubmit = async () => {
    if (submitting) return;

    const errors = validateEvacuationForm({
      location: locationText,
      numberOfPeople,
      emergencyType: selectedEmergency as any,
      hasVulnerable,
      contactName,
      contactPhone,
      additionalInfo,
    });

    const firstError = firstEvacuationError(errors);
    if (firstError) {
      const validationKeyMap: Record<string, TranslationKey> = {
        'Location is required.': 'validation.locationRequired',
        'Please enter the number of people.': 'validation.numberOfPeopleRequired',
        'Please select the type of emergency.': 'validation.emergencyTypeRequired',
        'Contact name is required.': 'validation.contactNameRequired',
        'Contact phone number is required.': 'validation.contactPhoneRequired',
      };
      const mapped = validationKeyMap[firstError];
      Alert.alert(t('common.required'), mapped ? t(mapped) : firstError);
      return;
    }

    setSubmitting(true);
    
    const request = addEvacuationRequest({
      location: locationText,
      numberOfPeople,
      emergencyType: selectedEmergency as any,
      hasVulnerable,
      contactName,
      contactPhone,
      additionalInfo,
      gpsCoords: location || undefined,
    });

    const syncResult = await syncToBackend(request);
    
    setSubmitting(false);
    setSubmitted(true);
    
    if (syncResult.serverConfirmed) {
      Alert.alert(
        t('callForEvacuation.sentTitle'),
        t('callForEvacuation.sentMessage', { backendMessage: t('callForEvacuation.serverConfirmed') }),
        [{ text: t('common.ok'), onPress: () => navigation.goBack() }]
      );
    } else {
      Alert.alert(
        t('callForEvacuation.offlineTitle'),
        t('callForEvacuation.offlineMessage'),
        [
          { text: t('common.ok'), onPress: () => navigation.goBack() },
          {
            text: t('common.call112'),
            onPress: async () => {
              try {
                await Linking.openURL('tel:112');
              } catch {
                // Ignore dialer failure safely
              }
              navigation.goBack();
            },
          },
        ]
      );
    }
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
          <Text style={styles.headerTitle}>{t('callForEvacuation.title')}</Text>
          <View style={{ width: 32 }} />
        </View>

        <Text style={styles.screenSubtitle}>
          {t('callForEvacuation.subtitle')}
        </Text>

        <View style={styles.sosSection}>
          <EmergencyButton onSOSActivated={handleSOS} size={120} disabled={sosState !== 'idle'} />
          <Text style={styles.sosHint}>{t('callForEvacuation.sosHint')}</Text>
        </View>

        <View style={styles.formSection}>
          <Text style={styles.sectionTitle}>{t('callForEvacuation.details')}</Text>

          <View style={styles.locationCard}>
            <View style={styles.locationHeader}>
              <Ionicons name="location" size={18} color={colors.primary} />
              <Text style={styles.locationLabel}>{t('callForEvacuation.currentLocation')}</Text>
            </View>
            <InputField
              placeholder={t('callForEvacuation.locationPlaceholder')}
              value={locationText}
              onChangeText={setLocationText}
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
                {getLocationDisplayText() || t('callForEvacuation.useCurrentLocation')}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.shareLocationBtn,
                (shareState === 'getting_location' || shareState === 'sharing') && styles.shareLocationBtnLoading,
              ]}
              onPress={shareLocation}
              disabled={shareState === 'getting_location' || shareState === 'sharing'}
            >
              {shareState === 'getting_location' || shareState === 'sharing' ? (
                <ActivityIndicator size={14} color={colors.textLight} />
              ) : (
                <Ionicons name="share-social-outline" size={14} color={colors.primary} />
              )}
              <Text style={[
                styles.shareLocationBtnText,
                (shareState === 'getting_location' || shareState === 'sharing') && styles.shareLocationBtnTextLoading,
              ]}>
                {shareState === 'getting_location' ? t('common.gettingLocation') : t('common.shareLocation')}
              </Text>
            </TouchableOpacity>
          </View>

          <InputField
            label={t('callForEvacuation.peopleNeedingEvacuation')}
            placeholder={t('callForEvacuation.peoplePlaceholder')}
            value={numberOfPeople}
            onChangeText={setNumberOfPeople}
            keyboardType="numeric"
            icon="people-outline"
          />

          <Text style={styles.fieldLabel}>{t('callForEvacuation.typeOfEmergency')}</Text>
          <View style={styles.chipContainer}>
            {EMERGENCY_TYPES.map((type) => (
              <TouchableOpacity
                key={type.key}
                style={[
                  styles.chip,
                  selectedEmergency === type.key && styles.chipActive,
                ]}
                onPress={() => setSelectedEmergency(type.key)}
              >
                <Ionicons
                  name={type.icon as any}
                  size={16}
                  color={selectedEmergency === type.key ? colors.white : colors.primary}
                />
                <Text
                  style={[
                    styles.chipText,
                    selectedEmergency === type.key && styles.chipTextActive,
                  ]}
                >
                  {t(EMERGENCY_TYPE_LABEL_KEYS[type.key] ?? 'callForEvacuation.emergencyTypes.other')}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.fieldLabel}>{t('callForEvacuation.vulnerable')}</Text>
          <View style={styles.radioRow}>
            <TouchableOpacity
              style={[styles.radioOption, hasVulnerable === true && styles.radioActive]}
              onPress={() => setHasVulnerable(true)}
            >
              <View style={[styles.radioDot, hasVulnerable === true && styles.radioDotActive]} />
              <Text style={[styles.radioLabel, hasVulnerable === true && styles.radioLabelActive]}>
                {t('common.yes')}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.radioOption, hasVulnerable === false && styles.radioActive]}
              onPress={() => setHasVulnerable(false)}
            >
              <View style={[styles.radioDot, hasVulnerable === false && styles.radioDotActive]} />
              <Text style={[styles.radioLabel, hasVulnerable === false && styles.radioLabelActive]}>
                {t('common.no')}
              </Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.sectionTitle}>{t('callForEvacuation.contactInformation')}</Text>

          <InputField
            label={t('callForEvacuation.contactName')}
            placeholder={t('callForEvacuation.contactNamePlaceholder')}
            value={contactName}
            onChangeText={setContactName}
            icon="person-outline"
          />

          <InputField
            label={t('callForEvacuation.phoneNumber')}
            placeholder={t('callForEvacuation.phoneNumberPlaceholder')}
            value={contactPhone}
            onChangeText={setContactPhone}
            keyboardType="phone-pad"
            icon="call-outline"
          />

          <InputField
            label={t('callForEvacuation.additionalInfo')}
            placeholder={t('callForEvacuation.additionalInfoPlaceholder')}
            value={additionalInfo}
            onChangeText={setAdditionalInfo}
            icon="chatbubble-outline"
          />

          <AppButton
            title={submitting ? t('callForEvacuation.submitting') : t('callForEvacuation.submitRequest')}
            onPress={handleSubmit}
            loading={submitting}
            disabled={submitted}
            style={styles.submitBtn}
          />

          <AppButton
            title={t('callForEvacuation.cancel')}
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
  sosSection: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
    backgroundColor: colors.sosBackground,
    marginHorizontal: spacing.base,
    borderRadius: borderRadius.xl,
    marginBottom: spacing.xl,
  },
  sosHint: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
  formSection: {
    paddingHorizontal: spacing.base,
  },
  sectionTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    marginBottom: spacing.md,
    marginTop: spacing.sm,
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
  shareLocationBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.base,
    borderRadius: borderRadius.round,
    backgroundColor: colors.white,
    marginTop: spacing.sm,
    borderWidth: 1,
    borderColor: colors.primary + '30',
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