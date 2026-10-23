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
import { useLocalRequests } from '../hooks/useLocalRequests';
import { useCurrentLocation } from '../hooks/useCurrentLocation';
import { useSOS } from '../hooks/useSOS';
import { useLocationShare } from '../hooks/useLocationShare';
import {
  validateReliefForm,
  firstReliefError,
} from '../services/relief/workflow';
import { useLanguage, type TranslationKey } from '../i18n';

interface RequestReliefScreenProps {
  navigation: any;
}

const RELIEF_CATEGORIES = [
  { key: 'food', labelKey: 'requestRelief.categories.food', descKey: 'requestRelief.categories.foodDesc', icon: 'water-outline' },
  { key: 'medical', labelKey: 'requestRelief.categories.medical', descKey: 'requestRelief.categories.medicalDesc', icon: 'medkit-outline' },
  { key: 'shelter', labelKey: 'requestRelief.categories.shelter', descKey: 'requestRelief.categories.shelterDesc', icon: 'home-outline' },
  { key: 'clothing', labelKey: 'requestRelief.categories.clothing', descKey: 'requestRelief.categories.clothingDesc', icon: 'shirt-outline' },
  { key: 'other', labelKey: 'requestRelief.categories.other', descKey: 'requestRelief.categories.otherDesc', icon: 'cube-outline' },
] as const;

const SEVERITY_LEVELS = [
  { key: 'low', labelKey: 'requestRelief.severity.low', descKey: 'requestRelief.severity.lowDesc', color: '#4CAF50' },
  { key: 'medium', labelKey: 'requestRelief.severity.medium', descKey: 'requestRelief.severity.mediumDesc', color: '#FF9800' },
  { key: 'high', labelKey: 'requestRelief.severity.high', descKey: 'requestRelief.severity.highDesc', color: '#FF5722' },
  { key: 'critical', labelKey: 'requestRelief.severity.critical', descKey: 'requestRelief.severity.criticalDesc', color: '#D32F2F' },
] as const;

export function RequestReliefScreen({ navigation }: RequestReliefScreenProps) {
  const { addReliefRequest, syncToBackend } = useLocalRequests();
  const { location, state: locationState, error: locationError, address, getLocation } = useCurrentLocation();
  const { activateSOS, state: sosState } = useSOS();
  const { shareState, shareLocation } = useLocationShare();
  const { t } = useLanguage();

  const [locationText, setLocationText] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [requiredItems, setRequiredItems] = useState('');
  const [quantity, setQuantity] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('');
  const [peopleAffected, setPeopleAffected] = useState('');
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

  const handleUseCurrentLocation = () => {
    getLocation();
  };

  const getLocationDisplayText = () => {
    if (locationState === 'locating') return t('emergencyCenter.gettingLocation');
    if (locationState === 'requesting_permission') return t('emergencyCenter.requestingPermission');
    if (locationState === 'success') {
      if (address) return t('requestRelief.locationDetected');
      if (location) return t('requestRelief.locationDetectedNoAddress');
      return t('requestRelief.locationDetected');
    }
    if (locationState === 'permission_denied') return t('requestRelief.locationPermissionNeeded');
    if (locationState === 'error') return locationError || t('requestRelief.locationError');
    return null;
  };

  const handleSubmit = async () => {
    if (submitting) return;

    const errors = validateReliefForm({
      location: locationText,
      reliefCategory: selectedCategory,
      requiredItems,
      quantity,
      peopleAffected,
      severity: selectedSeverity as 'low' | 'medium' | 'high' | 'critical' | '',
      hasVulnerable,
      contactName,
      contactPhone,
      additionalInfo,
    });

    const firstError = firstReliefError(errors);
    if (firstError) {
      const validationKeyMap: Record<string, TranslationKey> = {
        'Location is required.': 'validation.locationRequired',
        'Please select a relief category.': 'validation.reliefCategoryRequired',
        'Please describe the items or assistance needed.': 'validation.requiredItemsRequired',
        'Quantity is required.': 'validation.quantityRequired',
        'Please enter the number of people affected.': 'validation.peopleAffectedRequired',
        'Please select a severity level.': 'validation.severityRequired',
        'Contact name is required.': 'validation.contactNameRequired',
        'Contact phone number is required.': 'validation.contactPhoneRequired',
      };
      const mapped = validationKeyMap[firstError];
      Alert.alert(t('common.required'), mapped ? t(mapped) : firstError);
      return;
    }

    setSubmitting(true);

    const request = addReliefRequest({
      location: locationText,
      reliefCategory: selectedCategory,
      requiredItems,
      quantity,
      peopleAffected,
      severity: selectedSeverity as any,
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
        t('requestRelief.sentTitle'),
        t('requestRelief.sentMessage', { backendMessage: t('requestRelief.serverConfirmed') }),
        [{ text: t('common.ok'), onPress: () => navigation.goBack() }]
      );
    } else {
      Alert.alert(
        t('requestRelief.offlineTitle'),
        t('requestRelief.offlineMessage'),
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
          <Text style={styles.headerTitle}>{t('requestRelief.title')}</Text>
          <View style={{ width: 32 }} />
        </View>

        <Text style={styles.screenSubtitle}>
          {t('requestRelief.subtitle')}
        </Text>

        <Card style={styles.infoCard}>
          <Ionicons name="nutrition-outline" size={36} color={colors.primary} />
          <View style={styles.infoContent}>
            <Text style={styles.infoTitle}>{t('requestRelief.howItWorks')}</Text>
            <Text style={styles.infoText}>
              {t('requestRelief.howItWorksText')}
            </Text>
          </View>
        </Card>

        <View style={styles.sosSection}>
          <EmergencyButton onSOSActivated={activateSOS} size={120} disabled={sosState !== 'idle'} />
          <Text style={styles.sosHint}>{t('requestRelief.sosHint')}</Text>
        </View>

        <View style={styles.formSection}>
          <Text style={styles.sectionTitle}>{t('requestRelief.details')}</Text>

          <View style={styles.locationCard}>
            <View style={styles.locationHeader}>
              <Ionicons name="location" size={18} color={colors.primary} />
              <Text style={styles.locationLabel}>{t('requestRelief.yourLocation')}</Text>
            </View>
            <InputField
              placeholder={t('requestRelief.locationPlaceholder')}
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
                {getLocationDisplayText() || t('requestRelief.useCurrentLocation')}
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

          <Text style={styles.fieldLabel}>{t('requestRelief.whatTypeRelief')}</Text>
          <View style={styles.categoryContainer}>
            {RELIEF_CATEGORIES.map((cat) => {
              const isSelected = selectedCategory === cat.key;
              return (
                <TouchableOpacity
                  key={cat.key}
                  style={[styles.categoryCard, isSelected && styles.categoryCardActive]}
                  onPress={() => setSelectedCategory(cat.key)}
                  activeOpacity={0.7}
                >
                  <View style={[styles.categoryIconWrap, isSelected && styles.categoryIconWrapActive]}>
                    <Ionicons
                      name={cat.icon as any}
                      size={22}
                      color={isSelected ? colors.white : colors.primary}
                    />
                  </View>
                  <View style={styles.categoryInfo}>
                    <Text style={[styles.categoryLabel, isSelected && styles.categoryLabelActive]}>
                      {t(cat.labelKey)}
                    </Text>
                    <Text style={styles.categoryDesc}>{t(cat.descKey)}</Text>
                  </View>
                  {isSelected && (
                    <Ionicons name="checkmark-circle" size={22} color={colors.white} />
                  )}
                </TouchableOpacity>
              );
            })}
          </View>

          <InputField
            label={t('requestRelief.requiredItems')}
            placeholder={t('requestRelief.requiredItemsPlaceholder')}
            value={requiredItems}
            onChangeText={setRequiredItems}
            icon="clipboard-outline"
          />

          <InputField
            label={t('requestRelief.quantityLabel')}
            placeholder={t('requestRelief.quantityPlaceholder')}
            value={quantity}
            onChangeText={setQuantity}
            icon="calculator-outline"
          />

          <InputField
            label={t('requestRelief.peopleAffected')}
            placeholder={t('requestRelief.peopleAffectedPlaceholder')}
            value={peopleAffected}
            onChangeText={setPeopleAffected}
            keyboardType="numeric"
            icon="people-outline"
          />

          <Text style={styles.fieldLabel}>{t('requestRelief.vulnerable')}</Text>
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

          <Text style={styles.fieldLabel}>{t('requestRelief.severityLevel')}</Text>
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
            label={t('requestRelief.additionalInfo')}
            placeholder={t('requestRelief.additionalInfoPlaceholder')}
            value={additionalInfo}
            onChangeText={setAdditionalInfo}
            icon="chatbubble-outline"
          />

          <Text style={styles.sectionTitle}>{t('requestRelief.contactInformation')}</Text>

          <InputField
            label={t('requestRelief.contactName')}
            placeholder={t('requestRelief.contactNamePlaceholder')}
            value={contactName}
            onChangeText={setContactName}
            icon="person-outline"
          />

          <InputField
            label={t('requestRelief.phoneNumber')}
            placeholder={t('requestRelief.phoneNumberPlaceholder')}
            value={contactPhone}
            onChangeText={setContactPhone}
            keyboardType="phone-pad"
            icon="call-outline"
          />

          <AppButton
            title={submitting ? t('requestRelief.sending') : t('requestRelief.sendRequest')}
            onPress={handleSubmit}
            loading={submitting}
            disabled={submitted}
            style={styles.submitBtn}
          />

          <AppButton
            title={t('requestRelief.cancel')}
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
  categoryContainer: {
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  categoryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.lg,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.white,
  },
  categoryCardActive: {
    borderColor: colors.primary,
    backgroundColor: colors.primary,
  },
  categoryIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.sosBackground,
    alignItems: 'center',
    justifyContent: 'center',
  },
  categoryIconWrapActive: {
    backgroundColor: 'rgba(255,255,255,0.25)',
  },
  categoryInfo: {
    flex: 1,
  },
  categoryLabel: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  categoryLabelActive: {
    color: colors.white,
  },
  categoryDesc: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
    marginTop: 2,
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
});