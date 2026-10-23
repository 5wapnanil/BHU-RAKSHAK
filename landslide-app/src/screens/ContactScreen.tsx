import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Linking,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Card } from '../components';
import { colors } from '../theme/colors';
import { typography, spacing, borderRadius } from '../theme';
import { useLocationShare } from '../hooks/useLocationShare';
import { useLanguage, type TranslationKey } from '../i18n';
import {
  SEVEN_SISTERS,
  ONE_TAP_SERVICES,
  EMERGENCY_DIRECTORY,
  SITUATIONS,
  getOneTapNumber,
  getSituationContact,
  type SevenSistersState,
  type OneTapKey,
  type SituationInfo,
  type EmergencyCircleContact,
  RELATIONSHIP_OPTIONS,
} from '../constants/emergencyContacts';

const EMERGENCY_CIRCLE_KEY = '@aidconnect_emergency_circle';

async function loadEmergencyCircle(): Promise<EmergencyCircleContact[]> {
  try {
    const raw = await AsyncStorage.getItem(EMERGENCY_CIRCLE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

async function saveEmergencyCircle(contacts: EmergencyCircleContact[]): Promise<void> {
  try {
    await AsyncStorage.setItem(EMERGENCY_CIRCLE_KEY, JSON.stringify(contacts));
  } catch {
    // silently fail
  }
}

async function handleCall(number: string, t: (key: TranslationKey, params?: Record<string, string | number>) => string): Promise<void> {
  if (!number || number.trim().length === 0) {
    Alert.alert(t('contact.invalidNumber'), t('contact.noPhoneForService'));
    return;
  }
  try {
    const url = `tel:${number}`;
    const supported = await Linking.canOpenURL(url);
    if (supported) {
      await Linking.openURL(url);
    } else {
      Alert.alert(t('contact.unableToOpenDialer'), t('contact.dialManually', { phone: number }));
    }
  } catch {
    Alert.alert(t('contact.unableToOpenDialer'), t('contact.dialManually', { phone: number }));
  }
}

function buildEmergencySMSMessage(t: (key: TranslationKey, params?: Record<string, string | number>) => string): string {
  return t('shareTemplates.emergencyContactMessage');
}

async function handleMessage(number: string, t: (key: TranslationKey, params?: Record<string, string | number>) => string): Promise<void> {
  if (!number || number.trim().length === 0) {
    Alert.alert(t('contact.invalidNumber'), t('contact.noPhoneForContact'));
    return;
  }
  const url = `sms:${number}?body=${encodeURIComponent(buildEmergencySMSMessage(t))}`;
  try {
    const supported = await Linking.canOpenURL(url);
    if (supported) {
      await Linking.openURL(url);
    } else {
      Alert.alert(t('contact.unableToOpenMessages'), t('contact.smsManually', { phone: number }));
    }
  } catch {
    Alert.alert(t('contact.unableToOpenMessages'), t('contact.smsManually', { phone: number }));
  }
}

const SITUATION_LABEL_KEYS: Record<string, TranslationKey> = {
  landslide: 'contact.situations.landslide',
  flood: 'contact.situations.flood',
  fire: 'contact.situations.fire',
  medical: 'contact.situations.medical',
  crime: 'contact.situations.crime',
  women: 'contact.situations.women',
  child: 'contact.situations.child',
  road: 'contact.situations.road',
  building: 'contact.situations.building',
  electrical: 'contact.situations.electrical',
  lifethreat: 'contact.situations.lifethreat',
};

const RELATIONSHIP_LABEL_KEYS: Record<string, TranslationKey> = {
  Family: 'contact.relationships.family',
  Friend: 'contact.relationships.friend',
  Doctor: 'contact.relationships.doctor',
  'Local Volunteer': 'contact.relationships.localVolunteer',
  Caregiver: 'contact.relationships.caregiver',
};

export function ContactScreen() {
  const [selectedState, setSelectedState] = useState<SevenSistersState>('Assam');
  const [selectedSituation, setSelectedSituation] = useState<SituationInfo | null>(null);
  const [emergencyCircle, setEmergencyCircle] = useState<EmergencyCircleContact[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({ name: '', relationship: 'Family', phone: '' });
  const { shareState, shareLocation } = useLocationShare();
  const { t } = useLanguage();

  useEffect(() => {
    loadEmergencyCircle().then(setEmergencyCircle);
  }, []);

  useEffect(() => {
    saveEmergencyCircle(emergencyCircle);
  }, [emergencyCircle]);

  const addContact = useCallback(() => {
    const name = formData.name.trim();
    const phone = formData.phone.trim();
    if (!name) {
      Alert.alert(t('contact.nameRequired'), t('contact.enterName'));
      return;
    }
    if (!phone) {
      Alert.alert(t('contact.phoneRequired'), t('contact.enterPhone'));
      return;
    }
    const newContact: EmergencyCircleContact = {
      id: Date.now().toString(),
      name,
      relationship: formData.relationship,
      phone,
    };
    setEmergencyCircle((prev) => [...prev, newContact]);
    setFormData({ name: '', relationship: 'Family', phone: '' });
    setShowAddForm(false);
  }, [formData, t]);

  const removeContact = useCallback((id: string) => {
    Alert.alert(t('contact.removeContact'), t('contact.removeContactMessage'), [
      { text: t('common.cancel'), style: 'cancel' },
      {
        text: t('contact.remove'),
        style: 'destructive',
        onPress: () => setEmergencyCircle((prev) => prev.filter((c) => c.id !== id)),
      },
    ]);
  }, [t]);

  const stateContacts = EMERGENCY_DIRECTORY[selectedState];

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        {/* HEADER */}
        <View style={styles.headerSection}>
          <Text style={styles.headerTitle}>{t('contact.title')}</Text>
          <Text style={styles.headerSubtitle}>{t('contact.subtitle')}</Text>
          <Text style={styles.headerDesc}>
            {t('contact.desc')}
          </Text>
        </View>

        {/* PRIMARY 112 CARD */}
        <TouchableOpacity
          style={styles.primaryCard}
          activeOpacity={0.8}
          onPress={() => handleCall('112', t)}
        >
          <View style={styles.primaryLeft}>
            <Text style={styles.primaryLabel}>{t('contact.emergencyResponse')}</Text>
            <Text style={styles.primaryNumber}>112</Text>
          </View>
          <View style={styles.primaryRight}>
            <Ionicons name="call" size={24} color={colors.white} />
            <Text style={styles.primaryCta}>{t('contact.callNow')}</Text>
          </View>
        </TouchableOpacity>

        {/* ONE-TAP EMERGENCY */}
        <Text style={styles.sectionTitle}>{t('contact.oneTapEmergency')}</Text>
        <View style={styles.oneTapGrid}>
          {ONE_TAP_SERVICES.map((svc) => {
            const number = getOneTapNumber(selectedState, svc.key);
            return (
              <TouchableOpacity
                key={svc.key}
                style={[styles.oneTapCard, { backgroundColor: svc.bgColor }]}
                activeOpacity={0.7}
                onPress={() => handleCall(number, t)}
              >
                <View style={[styles.oneTapIconWrap, { backgroundColor: svc.iconColor + '18' }]}>
                  <Ionicons name={svc.icon as any} size={26} color={svc.iconColor} />
                </View>
                <Text style={styles.oneTapLabel}>{svc.label}</Text>
                <Text style={styles.oneTapNumber}>{number}</Text>
                <View style={[styles.oneTapCall, { backgroundColor: svc.iconColor }]}>
                  <Ionicons name="call" size={14} color={colors.white} />
                  <Text style={styles.oneTapCallText}>{t('common.call')}</Text>
                </View>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* STATE SELECTOR */}
        <Text style={styles.sectionTitle}>{t('contact.selectYourState')}</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.stateRow}>
          {SEVEN_SISTERS.map((s) => {
            const isActive = s.key === selectedState;
            return (
              <TouchableOpacity
                key={s.key}
                style={[styles.stateChip, isActive && styles.stateChipActive]}
                activeOpacity={0.7}
                onPress={() => setSelectedState(s.key)}
              >
                <Text style={[styles.stateChipText, isActive && styles.stateChipTextActive]}>
                  {s.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {/* OFFICIAL EMERGENCY DIRECTORY */}
        <Text style={styles.sectionTitle}>{t('contact.officialDirectory')}</Text>
        <Text style={styles.sectionSubtext}>{selectedState}</Text>
        {stateContacts.map((contact, idx) => (
          <Card key={idx} style={styles.contactCard}>
            <View style={styles.contactRow}>
              <View style={[styles.contactIconWrap, { backgroundColor: colors.primary + '15' }]}>
                <Ionicons name={contact.icon as any} size={22} color={colors.primary} />
              </View>
              <View style={styles.contactInfo}>
                <Text style={styles.contactService}>{contact.service}</Text>
                {contact.phones.map((phone, pIdx) => (
                  <Text key={pIdx} style={styles.contactPhone}>{phone}</Text>
                ))}
                <View style={styles.contactMeta}>
                  <Ionicons name="checkmark-circle" size={14} color={colors.success} />
                  <Text style={styles.contactSource}>{t('contact.officialContact')}</Text>
                </View>
              </View>
              <TouchableOpacity
                style={styles.contactCallBtn}
                activeOpacity={0.7}
                onPress={() => handleCall(contact.phones[0], t)}
              >
                <Ionicons name="call" size={18} color={colors.white} />
                <Text style={styles.contactCallText}>{t('common.call')}</Text>
              </TouchableOpacity>
            </View>
          </Card>
        ))}

        {/* WHO SHOULD I CALL? */}
        <Text style={styles.sectionTitle}>{t('contact.whoShouldICall')}</Text>
        <Text style={styles.sectionDesc}>
          {t('contact.whoShouldICallDesc')}
        </Text>
        <View style={styles.situationGrid}>
          {SITUATIONS.map((sit) => {
            const isSelected = selectedSituation?.key === sit.key;
            return (
              <TouchableOpacity
                key={sit.key}
                style={[styles.situationChip, isSelected && styles.situationChipActive]}
                activeOpacity={0.7}
                onPress={() => setSelectedSituation(isSelected ? null : sit)}
              >
                <Text style={styles.situationEmoji}>{sit.emoji}</Text>
                <Text style={[styles.situationLabel, isSelected && styles.situationLabelActive]}>
                  {SITUATION_LABEL_KEYS[sit.key] ? t(SITUATION_LABEL_KEYS[sit.key]) : sit.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {selectedSituation && (
          <Card style={styles.recommendedCard}>
            <Text style={styles.recommendedBadge}>{t('contact.recommendedContact')}</Text>
            {(() => {
              const contact = getSituationContact(selectedState, selectedSituation);
              return (
                <View>
                  <Text style={styles.recommendedService}>{contact.service}</Text>
                  <Text style={styles.recommendedNumber}>{contact.phone}</Text>
                  <TouchableOpacity
                    style={styles.recommendedCallBtn}
                    activeOpacity={0.7}
                    onPress={() => handleCall(contact.phone, t)}
                  >
                    <Ionicons name="call" size={18} color={colors.white} />
                    <Text style={styles.recommendedCallText}>{t('contact.callLabel', { phone: contact.phone })}</Text>
                  </TouchableOpacity>
                </View>
              );
            })()}
          </Card>
        )}

        {/* OFFLINE READY */}
        <Card style={styles.offlineCard}>
          <View style={styles.offlineRow}>
            <Ionicons name="phone-portrait-outline" size={22} color={colors.success} />
            <Text style={styles.offlineTitle}>{t('contact.offlineReady')}</Text>
          </View>
          <Text style={styles.offlineText}>
            {t('contact.offlineReadyText')}
          </Text>
        </Card>

        {/* MY EMERGENCY CIRCLE */}
        <Text style={styles.sectionTitle}>{t('contact.myEmergencyCircle')}</Text>
        <Text style={styles.sectionDesc}>
          {t('contact.myEmergencyCircleDesc')}
        </Text>

        {emergencyCircle.map((contact) => (
          <Card key={contact.id} style={styles.circleCard}>
            <View style={styles.circleTopRow}>
              <View style={styles.circleAvatar}>
                <Ionicons name="person" size={20} color={colors.white} />
              </View>
              <View style={styles.circleInfo}>
                <Text style={styles.circleName}>{contact.name}</Text>
                <Text style={styles.circleRel}>{contact.relationship}</Text>
                <Text style={styles.circlePhone}>{contact.phone}</Text>
              </View>
              <TouchableOpacity
                style={styles.circleDeleteBtn}
                activeOpacity={0.7}
                onPress={() => removeContact(contact.id)}
              >
                <Ionicons name="trash-outline" size={18} color={colors.error} />
              </TouchableOpacity>
            </View>
            <View style={styles.circleActionRow}>
              <TouchableOpacity
                style={[styles.circleActionBtn, styles.circleCallAction]}
                activeOpacity={0.7}
                onPress={() => handleCall(contact.phone, t)}
              >
                <Ionicons name="call" size={14} color={colors.white} />
                <Text style={styles.circleActionText}>{t('common.call')}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.circleActionBtn, styles.circleMessageAction]}
                activeOpacity={0.7}
                onPress={() => handleMessage(contact.phone, t)}
              >
                <Ionicons name="chatbubble" size={14} color={colors.white} />
                <Text style={styles.circleActionText}>{t('common.message')}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.circleActionBtn, styles.circleShareAction]}
                activeOpacity={0.7}
                onPress={shareLocation}
                disabled={shareState === 'getting_location' || shareState === 'sharing'}
              >
                {shareState === 'getting_location' || shareState === 'sharing' ? (
                  <ActivityIndicator size={14} color={colors.white} />
                ) : (
                  <Ionicons name="location" size={14} color={colors.white} />
                )}
                <Text style={styles.circleActionText}>
                  {shareState === 'getting_location' ? t('common.getting') : t('common.shareLocation')}
                </Text>
              </TouchableOpacity>
            </View>
          </Card>
        ))}

        {!showAddForm ? (
          <TouchableOpacity
            style={styles.addContactBtn}
            activeOpacity={0.7}
            onPress={() => setShowAddForm(true)}
          >
            <Ionicons name="add-circle-outline" size={22} color={colors.primary} />
            <Text style={styles.addContactText}>{t('contact.addTrustedContact')}</Text>
          </TouchableOpacity>
        ) : (
          <Card style={styles.addFormCard}>
            <Text style={styles.addFormTitle}>{t('contact.addTrustedContactTitle')}</Text>

            <Text style={styles.formLabel}>{t('contact.name')}</Text>
            <TextInput
              style={styles.formInput}
              placeholder={t('contact.namePlaceholder')}
              placeholderTextColor={colors.textLight}
              value={formData.name}
              onChangeText={(val) => setFormData((p) => ({ ...p, name: val }))}
            />

            <Text style={styles.formLabel}>{t('contact.relationship')}</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.relRow}>
              {RELATIONSHIP_OPTIONS.map((rel) => {
                const isActive = formData.relationship === rel;
                const labelKey = RELATIONSHIP_LABEL_KEYS[rel];
                return (
                  <TouchableOpacity
                    key={rel}
                    style={[styles.relChip, isActive && styles.relChipActive]}
                    activeOpacity={0.7}
                    onPress={() => setFormData((p) => ({ ...p, relationship: rel }))}
                  >
                    <Text style={[styles.relChipText, isActive && styles.relChipTextActive]}>
                      {labelKey ? t(labelKey) : rel}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>

            <Text style={styles.formLabel}>{t('contact.phone')}</Text>
            <TextInput
              style={styles.formInput}
              placeholder={t('contact.phonePlaceholder')}
              placeholderTextColor={colors.textLight}
              value={formData.phone}
              onChangeText={(val) => setFormData((p) => ({ ...p, phone: val }))}
              keyboardType="phone-pad"
            />

            <View style={styles.formActions}>
              <TouchableOpacity
                style={styles.formCancelBtn}
                activeOpacity={0.7}
                onPress={() => {
                  setShowAddForm(false);
                  setFormData({ name: '', relationship: 'Family', phone: '' });
                }}
              >
                <Text style={styles.formCancelText}>{t('common.cancel')}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.formSaveBtn}
                activeOpacity={0.7}
                onPress={addContact}
              >
                <Text style={styles.formSaveText}>{t('contact.saveContact')}</Text>
              </TouchableOpacity>
            </View>
          </Card>
        )}

        {/* SAFETY INFORMATION */}
        <Text style={styles.sectionTitle}>{t('contact.beforeYouCall')}</Text>
        <View style={styles.safetyGrid}>
          <Card style={styles.safetyCard}>
            <Ionicons name="location-outline" size={24} color={colors.primary} />
            <Text style={styles.safetyTitle}>{t('contact.shareYourLocation')}</Text>
            <Text style={styles.safetyDesc}>{t('contact.shareYourLocationDesc')}</Text>
          </Card>
          <Card style={styles.safetyCard}>
            <Ionicons name="chatbubble-outline" size={24} color={colors.primary} />
            <Text style={styles.safetyTitle}>{t('contact.describeSituation')}</Text>
            <Text style={styles.safetyDesc}>{t('contact.describeSituationDesc')}</Text>
          </Card>
          <Card style={styles.safetyCard}>
            <Ionicons name="battery-half-outline" size={24} color={colors.primary} />
            <Text style={styles.safetyTitle}>{t('contact.saveBattery')}</Text>
            <Text style={styles.safetyDesc}>{t('contact.saveBatteryDesc')}</Text>
          </Card>
        </View>

        <Text style={styles.disclaimer}>
          {t('contact.disclaimer')}
        </Text>

        <View style={{ height: 32 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.backgroundLight,
  },
  scrollContent: {
    paddingBottom: 20,
  },
  headerSection: {
    paddingHorizontal: spacing.base,
    paddingTop: spacing.xl,
    paddingBottom: spacing.md,
  },
  headerTitle: {
    fontSize: typography.fontSize.xxl,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    letterSpacing: 1,
  },
  headerSubtitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.primary,
    marginTop: spacing.xs,
  },
  headerDesc: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginTop: spacing.xs,
    lineHeight: 18,
  },
  primaryCard: {
    flexDirection: 'row',
    backgroundColor: colors.primary,
    marginHorizontal: spacing.base,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xl,
  },
  primaryLeft: {
    flex: 1,
  },
  primaryLabel: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.white,
    opacity: 0.85,
    letterSpacing: 0.5,
  },
  primaryNumber: {
    fontSize: typography.fontSize.display,
    fontWeight: typography.fontWeight.extraBold,
    color: colors.white,
    marginTop: spacing.xxs,
  },
  primaryRight: {
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.md,
    gap: spacing.xs,
  },
  primaryCta: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.bold,
    color: colors.white,
    letterSpacing: 0.5,
  },
  sectionTitle: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    marginHorizontal: spacing.base,
    marginTop: spacing.xl,
    marginBottom: spacing.md,
    letterSpacing: 0.5,
  },
  sectionSubtext: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.primary,
    marginHorizontal: spacing.base,
    marginBottom: spacing.md,
  },
  sectionDesc: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginHorizontal: spacing.base,
    marginBottom: spacing.md,
    lineHeight: 18,
  },
  oneTapGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginHorizontal: spacing.base,
  },
  oneTapCard: {
    width: '48%' as any,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    alignItems: 'center',
  },
  oneTapIconWrap: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  oneTapLabel: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    textAlign: 'center',
  },
  oneTapNumber: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    marginTop: spacing.xxs,
  },
  oneTapCall: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    borderRadius: borderRadius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    marginTop: spacing.sm,
  },
  oneTapCallText: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.bold,
    color: colors.white,
  },
  stateRow: {
    paddingHorizontal: spacing.base,
    gap: spacing.sm,
  },
  stateChip: {
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.round,
    backgroundColor: colors.white,
    borderWidth: 1.5,
    borderColor: colors.border,
  },
  stateChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  stateChipText: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    letterSpacing: 0.3,
  },
  stateChipTextActive: {
    color: colors.white,
  },
  contactCard: {
    marginHorizontal: spacing.base,
    marginBottom: spacing.sm,
  },
  contactRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  contactIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  contactInfo: {
    flex: 1,
  },
  contactService: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  contactPhone: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    color: colors.textSecondary,
    marginTop: spacing.xxs,
  },
  contactMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    marginTop: spacing.xs,
  },
  contactSource: {
    fontSize: typography.fontSize.xs,
    color: colors.success,
  },
  contactCallBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    backgroundColor: colors.primary,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  contactCallText: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.bold,
    color: colors.white,
  },
  situationGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginHorizontal: spacing.base,
  },
  situationChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.round,
    backgroundColor: colors.white,
    borderWidth: 1.5,
    borderColor: colors.border,
  },
  situationChipActive: {
    backgroundColor: colors.primary + '15',
    borderColor: colors.primary,
  },
  situationEmoji: {
    fontSize: typography.fontSize.base,
  },
  situationLabel: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.medium,
    color: colors.text,
  },
  situationLabelActive: {
    color: colors.primary,
    fontWeight: typography.fontWeight.semiBold,
  },
  recommendedCard: {
    marginHorizontal: spacing.base,
    marginTop: spacing.md,
    borderLeftWidth: 4,
    borderLeftColor: colors.primary,
  },
  recommendedBadge: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.bold,
    color: colors.primary,
    letterSpacing: 0.5,
    marginBottom: spacing.sm,
  },
  recommendedService: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  recommendedNumber: {
    fontSize: typography.fontSize.xxl,
    fontWeight: typography.fontWeight.bold,
    color: colors.primary,
    marginTop: spacing.xs,
  },
  recommendedCallBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.primary,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.md,
    marginTop: spacing.md,
    alignSelf: 'flex-start',
  },
  recommendedCallText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.bold,
    color: colors.white,
  },
  offlineCard: {
    marginHorizontal: spacing.base,
    marginTop: spacing.xl,
    backgroundColor: colors.successLight,
    borderLeftWidth: 4,
    borderLeftColor: colors.success,
  },
  offlineRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  offlineTitle: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.bold,
    color: colors.success,
    letterSpacing: 0.5,
  },
  offlineText: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    lineHeight: 18,
  },
  circleCard: {
    marginHorizontal: spacing.base,
    marginBottom: spacing.sm,
  },
  circleTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    marginBottom: spacing.sm,
  },
  circleAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  circleInfo: {
    flex: 1,
  },
  circleName: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  circleRel: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
    marginTop: spacing.xxs,
  },
  circlePhone: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    color: colors.text,
    marginTop: spacing.xxs,
  },
  circleDeleteBtn: {
    padding: spacing.sm,
  },
  circleActionRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.borderLight,
    paddingTop: spacing.sm,
  },
  circleActionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
    borderRadius: borderRadius.md,
    paddingVertical: spacing.sm,
  },
  circleCallAction: {
    backgroundColor: colors.success,
  },
  circleMessageAction: {
    backgroundColor: colors.info,
  },
  circleShareAction: {
    backgroundColor: colors.primary,
  },
  circleActionText: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.bold,
    color: colors.white,
  },
  addContactBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginHorizontal: spacing.base,
    marginTop: spacing.sm,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.base,
    borderRadius: borderRadius.md,
    borderWidth: 1.5,
    borderColor: colors.primary,
    borderStyle: 'dashed',
  },
  addContactText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.primary,
  },
  addFormCard: {
    marginHorizontal: spacing.base,
    marginTop: spacing.md,
  },
  addFormTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    marginBottom: spacing.base,
  },
  formLabel: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  formInput: {
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    fontSize: typography.fontSize.base,
    color: colors.text,
    backgroundColor: colors.white,
    marginBottom: spacing.md,
  },
  relRow: {
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  relChip: {
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.round,
    backgroundColor: colors.white,
    borderWidth: 1.5,
    borderColor: colors.border,
  },
  relChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  relChipText: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.medium,
    color: colors.text,
  },
  relChipTextActive: {
    color: colors.white,
  },
  formActions: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.sm,
  },
  formCancelBtn: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    borderWidth: 1.5,
    borderColor: colors.border,
  },
  formCancelText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.textSecondary,
  },
  formSaveBtn: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    backgroundColor: colors.primary,
  },
  formSaveText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.white,
  },
  safetyGrid: {
    gap: spacing.sm,
    marginHorizontal: spacing.base,
  },
  safetyCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.md,
    paddingVertical: spacing.md,
  },
  safetyTitle: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    marginTop: spacing.xxs,
  },
  safetyDesc: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
    lineHeight: 16,
    flex: 1,
  },
  disclaimer: {
    fontSize: typography.fontSize.xs,
    color: colors.textLight,
    fontStyle: 'italic',
    marginHorizontal: spacing.base,
    marginTop: spacing.xl,
    textAlign: 'center',
  },
});
