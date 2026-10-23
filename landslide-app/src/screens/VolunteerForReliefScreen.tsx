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
  validateReliefVolunteerForm,
  firstReliefVolunteerError,
} from '../services/volunteers/workflow';

interface VolunteerForReliefScreenProps {
  navigation: any;
}

const RELIEF_CATEGORIES = [
  { key: 'food', labelKey: 'volunteer.categories.food', icon: 'water-outline', descKey: 'volunteer.categories.foodDesc' },
  { key: 'medical', labelKey: 'volunteer.categories.medical', icon: 'medkit-outline', descKey: 'volunteer.categories.medicalDesc' },
  { key: 'shelter', labelKey: 'volunteer.categories.shelter', icon: 'home-outline', descKey: 'volunteer.categories.shelterDesc' },
  { key: 'clothing', labelKey: 'volunteer.categories.clothing', icon: 'shirt-outline', descKey: 'volunteer.categories.clothingDesc' },
  { key: 'transport', labelKey: 'volunteer.categories.transport', icon: 'car-outline', descKey: 'volunteer.categories.transportDesc' },
  { key: 'communication', labelKey: 'volunteer.categories.communication', icon: 'radio-outline', descKey: 'volunteer.categories.communicationDesc' },
] as const;

const AVAILABILITY_OPTIONS = [
  { value: 'Immediately', labelKey: 'common.immediately' },
  { value: 'Next 2 hours', labelKey: 'common.next2Hours' },
  { value: 'Next 6 hours', labelKey: 'common.next6Hours' },
  { value: 'Tomorrow', labelKey: 'common.tomorrow' },
  { value: 'Weekend only', labelKey: 'common.weekendOnly' },
] as const;

export function VolunteerForReliefScreen({ navigation }: VolunteerForReliefScreenProps) {
  const { addReliefVolunteer, syncToBackend } = useLocalRequests();
  const { location, state: locationState, error: locationError, address, getLocation } = useCurrentLocation();
  const { t } = useLanguage();

  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [locationText, setLocationText] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [quantity, setQuantity] = useState('');
  const [availability, setAvailability] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

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

    const errors = validateReliefVolunteerForm({
      name,
      phone,
      location: locationText,
      category: selectedCategory,
      quantity,
      availability,
      description,
    });

    const firstError = firstReliefVolunteerError(errors);
    if (firstError) {
      const validationKeyMap: Record<string, TranslationKey> = {
        'Name is required.': 'validation.volunteerNameRequired',
        'Phone number is required.': 'validation.volunteerPhoneRequired',
        'Location is required.': 'validation.volunteerLocationRequired',
        'Please select a category.': 'validation.categoryRequired',
        'Quantity / capacity is required.': 'validation.volunteerQuantityRequired',
        'Please select your availability.': 'validation.availabilityRequired',
        'Please provide a description.': 'validation.volunteerDescriptionRequired',
      };
      const mapped = validationKeyMap[firstError];
      Alert.alert(t('common.required'), mapped ? t(mapped) : firstError);
      return;
    }

    setSubmitting(true);
    
    const request = addReliefVolunteer({
      name,
      phone,
      location: locationText,
      category: selectedCategory,
      quantity,
      availability,
      description,
      gpsCoords: location || undefined,
    });

    const syncResult = await syncToBackend(request);
    
    setSubmitting(false);
    
    const backendMessage = syncResult.serverConfirmed
      ? t('volunteer.serverConfirmed')
      : t('volunteer.savedLocally');
    
    Alert.alert(
      t('volunteer.registeredTitle'),
      t('volunteer.registeredReliefMessage', { backendMessage }),
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
          <Text style={styles.headerTitle}>{t('volunteer.reliefTitle')}</Text>
          <View style={{ width: 32 }} />
        </View>

        <Text style={styles.screenSubtitle}>
          {t('volunteer.reliefSubtitle')}
        </Text>

        <Card style={styles.infoCard}>
          <Ionicons name="heart-outline" size={36} color={colors.primary} />
          <Text style={styles.infoTitle}>{t('volunteer.reliefInfoTitle')}</Text>
          <Text style={styles.infoText}>
            {t('volunteer.reliefInfoText')}
          </Text>
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
              <Text style={styles.locationLabel}>{t('volunteer.yourLocation')}</Text>
            </View>
            <InputField
              placeholder={t('volunteer.locationPlaceholder')}
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
                {getLocationDisplayText() || t('volunteer.useCurrentLocation')}
              </Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.sectionTitle}>{t('volunteer.reliefCategory')}</Text>
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
            label={t('volunteer.quantityCapacity')}
            placeholder={t('volunteer.quantityCapacityPlaceholder')}
            value={quantity}
            onChangeText={setQuantity}
            icon="clipboard-outline"
          />

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

          <InputField
            label={t('volunteer.additionalDetails')}
            placeholder={t('volunteer.additionalDetailsPlaceholder')}
            value={description}
            onChangeText={setDescription}
            icon="chatbubble-outline"
          />

          <AppButton
            title={submitting ? t('volunteer.registering') : t('volunteer.registerRelief')}
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
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  chip: {
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
  submitBtn: {
    marginTop: spacing.lg,
  },
  cancelBtn: {
    marginTop: spacing.sm,
  },
});