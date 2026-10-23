import React, { useState } from 'react';
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
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { EmergencyButton, AppButton, Card, InputField } from '../components';
import { colors } from '../theme/colors';
import { typography, spacing, borderRadius } from '../theme';
import { EMERGENCY_TYPES } from '../constants';
import { useLocalRequests } from '../hooks/useLocalRequests';
import { useCurrentLocation } from '../hooks/useCurrentLocation';
import { useSOS } from '../hooks/useSOS';
import { useLanguage, type TranslationKey } from '../i18n';
import {
  validateHelpForm,
  firstHelpError,
} from '../services/help/workflow';

interface CallForHelpScreenProps {
  navigation: any;
}

const SEVERITY_LEVELS = [
  { key: 'low', labelKey: 'callForHelp.severity.low' as TranslationKey, color: '#4CAF50', descKey: 'callForHelp.severity.lowDesc' as TranslationKey },
  { key: 'medium', labelKey: 'callForHelp.severity.medium' as TranslationKey, color: '#FF9800', descKey: 'callForHelp.severity.mediumDesc' as TranslationKey },
  { key: 'high', labelKey: 'callForHelp.severity.high' as TranslationKey, color: '#FF5722', descKey: 'callForHelp.severity.highDesc' as TranslationKey },
  { key: 'critical', labelKey: 'callForHelp.severity.critical' as TranslationKey, color: '#D32F2F', descKey: 'callForHelp.severity.criticalDesc' as TranslationKey },
];

const EMERGENCY_TYPE_LABEL_KEYS: Record<string, TranslationKey> = {
  fire: 'callForHelp.emergencyTypes.fire',
  earthquake: 'callForHelp.emergencyTypes.earthquake',
  flood: 'callForHelp.emergencyTypes.flood',
  landslide: 'callForHelp.emergencyTypes.landslide',
  cyclone: 'callForHelp.emergencyTypes.cyclone',
  other: 'callForHelp.emergencyTypes.other',
};

export function CallForHelpScreen({ navigation }: CallForHelpScreenProps) {
  const { addHelpRequest, syncToBackend } = useLocalRequests();
  const { location, state: locationState, error: locationError, getLocation } = useCurrentLocation();
  const { activateSOS, state: sosState } = useSOS();
  const { t } = useLanguage();

  const [locationText, setLocationText] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('');
  const [peopleAffected, setPeopleAffected] = useState('');
  const [description, setDescription] = useState('');
  const [contactName, setContactName] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSOS = () => {
    return activateSOS();
  };

  const handleUseCurrentLocation = () => {
    getLocation();
  };

  const getLocationDisplayText = () => {
    if (locationState === 'locating') return t('emergencyCenter.gettingLocation');
    if (locationState === 'requesting_permission') return t('emergencyCenter.requestingPermission');
    if (locationState === 'success' && location) {
      return `${location.latitude.toFixed(6)}, ${location.longitude.toFixed(6)}`;
    }
    if (locationState === 'permission_denied') return t('emergencyCenter.locationDenied');
    if (locationState === 'error') return locationError || t('emergencyCenter.locationUnavailable');
    return null;
  };

  const handleSubmit = async () => {
    if (submitting) return;

    const errors = validateHelpForm({
      location: locationText,
      category: selectedCategory as any,
      severity: selectedSeverity as any,
      peopleAffected,
      description,
      contactName,
      contactPhone,
    });

    const firstError = firstHelpError(errors);
    if (firstError) {
      const validationKeyMap: Record<string, TranslationKey> = {
        'Location is required.': 'validation.locationRequired',
        'Please select a category.': 'validation.reliefCategoryRequired',
        'Please select a severity level.': 'validation.severityRequired',
        'Please enter the number of people affected.': 'validation.peopleAffectedRequired',
        'Please describe the items or assistance needed.': 'validation.requiredItemsRequired',
        'Contact name is required.': 'validation.contactNameRequired',
        'Contact phone number is required.': 'validation.contactPhoneRequired',
      };
      const mapped = validationKeyMap[firstError];
      Alert.alert(t('common.required'), mapped ? t(mapped) : firstError);
      return;
    }

    setSubmitting(true);

    const request = addHelpRequest({
      location: locationText,
      category: selectedCategory as any,
      severity: selectedSeverity as any,
      peopleAffected,
      description,
      contactName,
      contactPhone,
      gpsCoords: location || undefined,
    });

    const syncResult = await syncToBackend(request);

    setSubmitting(false);
    setSubmitted(true);

    if (syncResult.serverConfirmed) {
      Alert.alert(
        t('callForHelp.sentTitle'),
        t('callForHelp.sentMessage', { backendMessage: t('callForHelp.serverConfirmed') }),
        [{ text: t('common.ok'), onPress: () => navigation.goBack() }]
      );
    } else {
      Alert.alert(
        t('callForHelp.offlineTitle'),
        t('callForHelp.offlineMessage'),
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
          <Text style={styles.headerTitle}>{t('callForHelp.title')}</Text>
          <View style={{ width: 32 }} />
        </View>

        <Text style={styles.screenSubtitle}>
          {t('callForHelp.subtitle')}
        </Text>

        <View style={styles.sosSection}>
          <EmergencyButton onSOSActivated={handleSOS} size={120} disabled={sosState !== 'idle'} />
          <Text style={styles.sosHint}>{t('callForHelp.sosHint')}</Text>
        </View>

        <Card style={styles.infoCard}>
          <Ionicons name="information-circle-outline" size={24} color={colors.primary} />
          <View style={styles.infoContent}>
            <Text style={styles.infoTitle}>{t('callForHelp.howItWorks')}</Text>
            <Text style={styles.infoText}>
              {t('callForHelp.howItWorksText')}
            </Text>
          </View>
        </Card>

        <View style={styles.formSection}>
          <Text style={styles.sectionTitle}>{t('callForHelp.details')}</Text>

          <Text style={styles.fieldLabel}>{t('callForHelp.whatTypeHelp')}</Text>
          <View style={styles.chipContainer}>
            {EMERGENCY_TYPES.map((type) => (
              <TouchableOpacity
                key={type.key}
                style={[styles.chip, selectedCategory === type.key && styles.chipActive]}
                onPress={() => setSelectedCategory(type.key)}
              >
                <Ionicons
                  name={type.icon as any}
                  size={16}
                  color={selectedCategory === type.key ? colors.white : colors.primary}
                />
                <Text style={[styles.chipText, selectedCategory === type.key && styles.chipTextActive]}>
                  {t(EMERGENCY_TYPE_LABEL_KEYS[type.key] ?? 'callForHelp.emergencyTypes.other')}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={styles.locationCard}>
            <View style={styles.locationHeader}>
              <Ionicons name="location" size={18} color={colors.primary} />
              <Text style={styles.locationLabel}>{t('callForHelp.yourLocation')}</Text>
            </View>
            <InputField
              placeholder={t('callForHelp.locationPlaceholder')}
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
                {getLocationDisplayText() || t('callForHelp.useCurrentLocation')}
              </Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.fieldLabel}>{t('callForHelp.severityLevel')}</Text>
          <View style={styles.severityContainer}>
            {SEVERITY_LEVELS.map((level) => {
              const isSelected = selectedSeverity === level.key;
              return (
                <TouchableOpacity
                  key={level.key}
                  style={[
                    styles.severityOption,
                    isSelected && { borderColor: level.color, backgroundColor: level.color + '15' },
                  ]}
                  onPress={() => setSelectedSeverity(level.key)}
                >
                  <View style={[styles.severityDot, { backgroundColor: level.color }]} />
                  <View style={styles.severityInfo}>
                    <Text style={[styles.severityLabel, isSelected && { color: level.color }]}>
                      {t(level.labelKey)}
                    </Text>
                    <Text style={styles.severityDesc}>{t(level.descKey)}</Text>
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>

          <InputField
            label={t('callForHelp.peopleAffected')}
            placeholder={t('callForHelp.peopleAffectedPlaceholder')}
            value={peopleAffected}
            onChangeText={setPeopleAffected}
            keyboardType="numeric"
            icon="people-outline"
          />

          <InputField
            label={t('callForHelp.descriptionLabel')}
            placeholder={t('callForHelp.descriptionPlaceholder')}
            value={description}
            onChangeText={setDescription}
            icon="chatbubble-outline"
          />

          <Text style={styles.sectionTitle}>{t('callForHelp.contactInformation')}</Text>

          <InputField
            label={t('callForHelp.contactName')}
            placeholder={t('callForHelp.contactNamePlaceholder')}
            value={contactName}
            onChangeText={setContactName}
            icon="person-outline"
          />

          <InputField
            label={t('callForHelp.phoneNumber')}
            placeholder={t('callForHelp.phoneNumberPlaceholder')}
            value={contactPhone}
            onChangeText={setContactPhone}
            keyboardType="phone-pad"
            icon="call-outline"
          />

          <AppButton
            title={submitting ? t('callForHelp.sending') : t('callForHelp.sendRequest')}
            onPress={handleSubmit}
            loading={submitting}
            disabled={submitted}
            style={styles.submitBtn}
          />

          <AppButton
            title={t('callForHelp.cancel')}
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
  infoCard: {
    marginHorizontal: spacing.base,
    flexDirection: 'row',
    gap: spacing.md,
    alignItems: 'flex-start',
  },
  infoContent: {
    flex: 1,
  },
  infoTitle: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  infoText: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    lineHeight: 20,
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
    marginTop: spacing.sm,
  },
  fieldLabel: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    marginBottom: spacing.sm,
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
  severityContainer: {
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  severityOption: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.white,
  },
  severityDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  severityInfo: {
    flex: 1,
  },
  severityLabel: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  severityDesc: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
    marginTop: 2,
  },
  submitBtn: {
    marginTop: spacing.lg,
  },
  cancelBtn: {
    marginTop: spacing.sm,
  },
});