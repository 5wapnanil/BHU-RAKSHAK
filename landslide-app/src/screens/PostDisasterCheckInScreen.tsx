import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Modal,
  TextInput,
  Share,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { colors } from '../theme/colors';
import { typography, spacing, borderRadius } from '../theme';
import { useCurrentLocation } from '../hooks/useCurrentLocation';
import { useLanguage } from '../i18n';
import type { EmergencyCircleContact } from '../constants/emergencyContacts';

const CHECKIN_STORAGE_KEY = '@aidconnect_last_checkin';
const CIRCLE_STORAGE_KEY = '@aidconnect_emergency_circle';

export type CheckInType = 'safe' | 'help' | 'missing';

export interface CheckInRecord {
  type: CheckInType;
  timestamp: string;
  latitude?: number;
  longitude?: number;
  address?: string | null;
  missingName?: string;
  missingRelationship?: string;
  missingNotes?: string;
}

interface PostDisasterCheckInScreenProps {
  navigation: any;
}

async function loadLastCheckIn(): Promise<CheckInRecord | null> {
  try {
    const raw = await AsyncStorage.getItem(CHECKIN_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as CheckInRecord) : null;
  } catch {
    return null;
  }
}

async function saveCheckIn(record: CheckInRecord): Promise<void> {
  try {
    await AsyncStorage.setItem(CHECKIN_STORAGE_KEY, JSON.stringify(record));
  } catch {
    // Non-blocking — check-in still shown for this session
  }
}

function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

export function PostDisasterCheckInScreen({ navigation }: PostDisasterCheckInScreenProps) {
  const [lastCheckIn, setLastCheckIn] = useState<CheckInRecord | null>(null);
  const [contacts, setContacts] = useState<EmergencyCircleContact[]>([]);
  const [showSafeConfirm, setShowSafeConfirm] = useState(false);
  const [safeState, setSafeState] = useState<'idle' | 'locating' | 'saving' | 'done'>('idle');
  const [showMissingForm, setShowMissingForm] = useState(false);
  const [missingName, setMissingName] = useState('');
  const [missingRelationship, setMissingRelationship] = useState('');
  const [missingNotes, setMissingNotes] = useState('');
  const [missingSaving, setMissingSaving] = useState(false);
  const { t } = useLanguage();

  const {
    location,
    state: locationState,
    error: locationError,
    address,
    getLocation,
  } = useCurrentLocation();

  useEffect(() => {
    loadLastCheckIn().then(setLastCheckIn);
    AsyncStorage.getItem(CIRCLE_STORAGE_KEY)
      .then((raw) => {
        if (raw) setContacts(JSON.parse(raw));
      })
      .catch(() => {});
  }, []);

  const handleSafeConfirm = useCallback(async () => {
    setShowSafeConfirm(false);
    setSafeState('locating');
    await getLocation();
  }, [getLocation]);

  useEffect(() => {
    if (safeState !== 'locating') return;
    if (locationState === 'permission_denied' || locationState === 'error') {
      Alert.alert(
        t('checkIn.locationUnavailable'),
        locationError || t('checkIn.locationUnavailableMessage'),
        [
          { text: t('common.retry'), onPress: () => getLocation() },
          {
            text: t('checkIn.markSafeAnyway'),
            onPress: async () => {
              const record: CheckInRecord = {
                type: 'safe',
                timestamp: new Date().toISOString(),
              };
              await saveCheckIn(record);
              setLastCheckIn(record);
              setSafeState('done');
            },
          },
          { text: t('common.cancel'), style: 'cancel', onPress: () => setSafeState('idle') },
        ],
      );
      return;
    }
    if (locationState === 'success' && location) {
      (async () => {
        setSafeState('saving');
        const record: CheckInRecord = {
          type: 'safe',
          timestamp: new Date().toISOString(),
          latitude: location.latitude,
          longitude: location.longitude,
          address,
        };
        await saveCheckIn(record);
        setLastCheckIn(record);
        setSafeState('done');
      })();
    }
  }, [safeState, locationState, location, address, locationError, getLocation, t]);

  const handleShareSafeWithCircle = useCallback(async () => {
    if (!lastCheckIn || lastCheckIn.type !== 'safe') return;
    const coordLine = lastCheckIn.latitude
      ? `\nCoordinates: ${lastCheckIn.latitude.toFixed(6)}, ${lastCheckIn.longitude?.toFixed(6)}`
      : '';
    const addressLine = lastCheckIn.address ? `\nLocation: ${lastCheckIn.address}` : '';
    const message =
      `✅ I'M SAFE\n\n` +
      `I have checked in as safe after the disaster.${addressLine}${coordLine}\n` +
      `Time: ${formatTimestamp(lastCheckIn.timestamp)}`;
    try {
      await Share.share({ message, title: 'Safety Check-In' }, { dialogTitle: 'Share safety status' });
    } catch {
      // User cancelled or share failed — non-blocking
    }
  }, [lastCheckIn]);

  const handleNeedHelp = useCallback(() => {
    navigation.navigate('RequestRelief');
  }, [navigation]);

  const handleMissingSubmit = useCallback(async () => {
    if (!missingName.trim()) {
      Alert.alert(t('checkIn.nameRequired'), t('checkIn.enterMissingName'));
      return;
    }
    setMissingSaving(true);
    const record: CheckInRecord = {
      type: 'missing',
      timestamp: new Date().toISOString(),
      missingName: missingName.trim(),
      missingRelationship: missingRelationship.trim() || undefined,
      missingNotes: missingNotes.trim() || undefined,
    };
    await saveCheckIn(record);
    setLastCheckIn(record);
    setMissingSaving(false);
    setShowMissingForm(false);
    setMissingName('');
    setMissingRelationship('');
    setMissingNotes('');

    const message =
      `🚨 ${t('shareTemplates.missingPersonHeading')}\n\n` +
      `${t('shareTemplates.missingPersonNameLabel')}: ${record.missingName}\n` +
      (record.missingRelationship ? `${t('shareTemplates.missingPersonRelationshipLabel')}: ${record.missingRelationship}\n` : '') +
      (record.missingNotes ? `${t('shareTemplates.missingPersonNotesLabel')}: ${record.missingNotes}\n` : '') +
      `${t('shareTemplates.missingPersonReportedLabel')}: ${formatTimestamp(record.timestamp)}\n\n` +
      t('shareTemplates.missingPersonMessage');
    try {
      await Share.share({ message, title: t('shareTemplates.missingPersonTitle') }, { dialogTitle: t('shareTemplates.missingPersonDialogTitle') });
    } catch {
      // Share cancelled — report still saved locally
    }
  }, [missingName, missingRelationship, missingNotes, t]);

  const handleCallContact = useCallback((phone: string) => {
    const url = `tel:${phone}`;
    Linking.canOpenURL(url).then((s) => s && Linking.openURL(url));
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backBtn}
          activeOpacity={0.7}
          onPress={() => navigation.goBack()}
        >
          <Ionicons name="arrow-back" size={22} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('checkIn.title')}</Text>
        <View style={styles.headerSpacer} />
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        <Text style={styles.intro}>
          {t('checkIn.intro')}
        </Text>

        {lastCheckIn && (
          <View
            style={[
              styles.lastCheckInBanner,
              lastCheckIn.type === 'safe' && styles.lastSafe,
              lastCheckIn.type === 'help' && styles.lastHelp,
              lastCheckIn.type === 'missing' && styles.lastMissing,
            ]}
          >
            <Ionicons
              name={
                lastCheckIn.type === 'safe'
                  ? 'checkmark-circle'
                  : lastCheckIn.type === 'help'
                    ? 'alert-circle'
                    : 'person'
              }
              size={20}
              color={
                lastCheckIn.type === 'safe'
                  ? colors.success
                  : lastCheckIn.type === 'help'
                    ? colors.warning
                    : colors.error
              }
            />
            <View style={styles.lastCheckInInfo}>
              <Text style={styles.lastCheckInLabel}>
                {t('checkIn.lastCheckIn')}{' '}
                {lastCheckIn.type === 'safe'
                  ? t('checkIn.imSafe')
                  : lastCheckIn.type === 'help'
                    ? t('checkIn.iNeedHelp')
                    : t('checkIn.missing', { name: lastCheckIn.missingName ?? '' })}
              </Text>
              <Text style={styles.lastCheckInTime}>{formatTimestamp(lastCheckIn.timestamp)}</Text>
              {lastCheckIn.address ? (
                <Text style={styles.lastCheckInAddress} numberOfLines={1}>
                  {lastCheckIn.address}
                </Text>
              ) : null}
            </View>
          </View>
        )}

        {/* I'M SAFE */}
        <TouchableOpacity
          style={[styles.actionCard, styles.safeCard]}
          activeOpacity={0.7}
          onPress={() => {
            if (safeState === 'locating' || safeState === 'saving') return;
            if (safeState === 'done') {
              Alert.alert(
                t('checkIn.alreadySafeTitle'),
                t('checkIn.alreadySafeMessage'),
                [
                  { text: t('common.cancel'), style: 'cancel' },
                  { text: t('checkIn.checkInAgain'), onPress: () => { setSafeState('idle'); setShowSafeConfirm(true); } },
                ],
              );
              return;
            }
            setShowSafeConfirm(true);
          }}
          disabled={safeState === 'locating' || safeState === 'saving'}
        >
          <View style={[styles.actionIconWrap, { backgroundColor: colors.successLight }]}>
            {safeState === 'locating' || safeState === 'saving' ? (
              <ActivityIndicator size="small" color={colors.success} />
            ) : (
              <Ionicons name="shield-checkmark-outline" size={30} color={colors.success} />
            )}
          </View>
          <View style={styles.actionContent}>
            <Text style={styles.actionTitle}>
              {safeState === 'locating'
                ? t('checkIn.gettingLocation')
                : safeState === 'saving'
                  ? t('checkIn.saving')
                  : t('checkIn.imSafe')}
            </Text>
            <Text style={styles.actionSubtitle}>
              {t('checkIn.imSafeDesc')}
            </Text>
          </View>
          {safeState === 'done' && (
            <Ionicons name="checkmark-circle" size={22} color={colors.success} />
          )}
        </TouchableOpacity>

        {safeState === 'done' && lastCheckIn?.type === 'safe' && (
          <TouchableOpacity
            style={styles.shareSafeBtn}
            activeOpacity={0.7}
            onPress={handleShareSafeWithCircle}
          >
            <Ionicons name="share-social-outline" size={16} color={colors.success} />
            <Text style={styles.shareSafeText}>{t('checkIn.shareSafe')}</Text>
          </TouchableOpacity>
        )}

        {/* I NEED HELP */}
        <TouchableOpacity
          style={[styles.actionCard, styles.helpCard]}
          activeOpacity={0.7}
          onPress={handleNeedHelp}
        >
          <View style={[styles.actionIconWrap, { backgroundColor: colors.warningLight }]}>
            <Ionicons name="hand-left-outline" size={30} color={colors.warning} />
          </View>
          <View style={styles.actionContent}>
            <Text style={styles.actionTitle}>{t('checkIn.iNeedHelp')}</Text>
            <Text style={styles.actionSubtitle}>
              {t('checkIn.iNeedHelpDesc')}
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color={colors.textLight} />
        </TouchableOpacity>

        {/* SOMEONE IS MISSING */}
        <TouchableOpacity
          style={[styles.actionCard, styles.missingCard]}
          activeOpacity={0.7}
          onPress={() => setShowMissingForm(true)}
        >
          <View style={[styles.actionIconWrap, { backgroundColor: colors.errorLight }]}>
            <Ionicons name="person-remove-outline" size={30} color={colors.error} />
          </View>
          <View style={styles.actionContent}>
            <Text style={styles.actionTitle}>{t('checkIn.someoneMissing')}</Text>
            <Text style={styles.actionSubtitle}>
              {t('checkIn.someoneMissingDesc')}
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color={colors.textLight} />
        </TouchableOpacity>

        {lastCheckIn?.type === 'missing' && (
          <View style={styles.missingReportBox}>
            <Text style={styles.missingReportTitle}>
              {t('checkIn.missingTitle', { name: lastCheckIn.missingName ?? '' })}
            </Text>
            {lastCheckIn.missingRelationship ? (
              <Text style={styles.missingReportLine}>
                {t('checkIn.relationshipLabel')} {lastCheckIn.missingRelationship}
              </Text>
            ) : null}
            {lastCheckIn.missingNotes ? (
              <Text style={styles.missingReportLine}>{lastCheckIn.missingNotes}</Text>
            ) : null}
          </View>
        )}

        {/* Emergency Circle quick call */}
        {contacts.length > 0 && (
          <View style={styles.circleSection}>
            <Text style={styles.circleTitle}>{t('checkIn.emergencyCircle')}</Text>
            {contacts.slice(0, 4).map((c) => (
              <TouchableOpacity
                key={c.id}
                style={styles.circleItem}
                activeOpacity={0.7}
                onPress={() => handleCallContact(c.phone)}
              >
                <View style={styles.circleAvatar}>
                  <Ionicons name="person" size={13} color={colors.white} />
                </View>
                <View style={styles.circleInfo}>
                  <Text style={styles.circleName}>{c.name}</Text>
                  <Text style={styles.circleRel}>{c.relationship}</Text>
                </View>
                <View style={styles.circleCallBtn}>
                  <Ionicons name="call" size={14} color={colors.white} />
                </View>
              </TouchableOpacity>
            ))}
          </View>
        )}

        <View style={{ height: 30 }} />
      </ScrollView>

      {/* Safe confirmation modal */}
      <Modal visible={showSafeConfirm} transparent animationType="fade" onRequestClose={() => setShowSafeConfirm(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalIconSafe}>
              <Ionicons name="shield-checkmark-outline" size={32} color={colors.success} />
            </View>
            <Text style={styles.modalTitle}>{t('checkIn.confirmSafeTitle')}</Text>
            <Text style={styles.modalBody}>
              {t('checkIn.confirmSafeBody')}
            </Text>
            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.modalCancelBtn}
                activeOpacity={0.7}
                onPress={() => setShowSafeConfirm(false)}
              >
                <Text style={styles.modalCancelText}>{t('common.cancel')}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.modalConfirmBtn}
                activeOpacity={0.7}
                onPress={handleSafeConfirm}
              >
                <Text style={styles.modalConfirmText}>{t('checkIn.confirmSafe')}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Missing person form modal */}
      <Modal visible={showMissingForm} transparent animationType="slide" onRequestClose={() => setShowMissingForm(false)}>
        <View style={styles.modalOverlay}>
          <View style={[styles.modalCard, styles.missingModalCard]}>
            <Text style={styles.modalTitle}>{t('checkIn.missingFormTitle')}</Text>
            <Text style={styles.modalBody}>
              {t('checkIn.missingFormBody')}
            </Text>

            <Text style={styles.fieldLabel}>{t('checkIn.nameLabel')}</Text>
            <TextInput
              style={styles.input}
              value={missingName}
              onChangeText={setMissingName}
              placeholder={t('checkIn.namePlaceholder')}
              placeholderTextColor={colors.textLight}
            />

            <Text style={styles.fieldLabel}>{t('contact.relationship')}</Text>
            <TextInput
              style={styles.input}
              value={missingRelationship}
              onChangeText={setMissingRelationship}
              placeholder={t('checkIn.relationshipPlaceholder')}
              placeholderTextColor={colors.textLight}
            />

            <Text style={styles.fieldLabel}>{t('checkIn.lastKnownDetails')}</Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              value={missingNotes}
              onChangeText={setMissingNotes}
              placeholder={t('checkIn.lastKnownPlaceholder')}
              placeholderTextColor={colors.textLight}
              multiline
              numberOfLines={3}
              textAlignVertical="top"
            />

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.modalCancelBtn}
                activeOpacity={0.7}
                onPress={() => setShowMissingForm(false)}
                disabled={missingSaving}
              >
                <Text style={styles.modalCancelText}>{t('common.cancel')}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalConfirmBtn, styles.missingConfirmBtn]}
                activeOpacity={0.7}
                onPress={handleMissingSubmit}
                disabled={missingSaving}
              >
                {missingSaving ? (
                  <ActivityIndicator size="small" color={colors.white} />
                ) : (
                  <Text style={styles.modalConfirmText}>{t('checkIn.saveShare')}</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
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
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.sm,
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.backgroundGray,
  },
  headerTitle: {
    flex: 1,
    textAlign: 'center',
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
  },
  headerSpacer: {
    width: 40,
  },
  scrollContent: {
    padding: spacing.base,
  },
  intro: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    lineHeight: 20,
    marginBottom: spacing.md,
  },
  lastCheckInBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.borderLight,
    padding: spacing.base,
    marginBottom: spacing.md,
    gap: spacing.sm,
  },
  lastSafe: {
    borderColor: colors.success,
    backgroundColor: colors.successLight,
  },
  lastHelp: {
    borderColor: colors.warning,
    backgroundColor: colors.warningLight,
  },
  lastMissing: {
    borderColor: colors.error,
    backgroundColor: colors.errorLight,
  },
  lastCheckInInfo: {
    flex: 1,
  },
  lastCheckInLabel: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
  },
  lastCheckInTime: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
    marginTop: 2,
  },
  lastCheckInAddress: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
    marginTop: 1,
  },
  actionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.borderLight,
    padding: spacing.base,
    marginBottom: spacing.md,
  },
  safeCard: {
    borderColor: colors.success,
  },
  helpCard: {
    borderColor: colors.warning,
  },
  missingCard: {
    borderColor: colors.error,
  },
  actionIconWrap: {
    width: 56,
    height: 56,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  actionContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    marginBottom: 2,
  },
  actionSubtitle: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    lineHeight: 18,
  },
  shareSafeBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    backgroundColor: colors.successLight,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.success,
    paddingVertical: spacing.sm,
    marginBottom: spacing.md,
  },
  shareSafeText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.success,
  },
  missingReportBox: {
    backgroundColor: colors.errorLight,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.error,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  missingReportTitle: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.bold,
    color: colors.error,
    marginBottom: spacing.xs,
  },
  missingReportLine: {
    fontSize: typography.fontSize.xs,
    color: colors.text,
    lineHeight: 18,
  },
  circleSection: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.borderLight,
    padding: spacing.base,
    marginBottom: spacing.md,
  },
  circleTitle: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    marginBottom: spacing.sm,
  },
  circleItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.borderLight,
    gap: spacing.sm,
  },
  circleAvatar: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  circleInfo: {
    flex: 1,
  },
  circleName: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  circleRel: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
  },
  circleCallBtn: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: colors.success,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: colors.overlay,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.base,
  },
  modalCard: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    width: '100%',
    maxWidth: 400,
    alignItems: 'center',
  },
  missingModalCard: {
    alignItems: 'stretch',
  },
  modalIconSafe: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: colors.successLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  modalTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  modalBody: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    lineHeight: 20,
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  modalActions: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  modalCancelBtn: {
    flex: 1,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
  },
  modalCancelText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.textSecondary,
  },
  modalConfirmBtn: {
    flex: 1,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    backgroundColor: colors.success,
    alignItems: 'center',
  },
  missingConfirmBtn: {
    backgroundColor: colors.error,
  },
  modalConfirmText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.bold,
    color: colors.white,
  },
  fieldLabel: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
    marginTop: spacing.sm,
  },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: typography.fontSize.sm,
    color: colors.text,
    backgroundColor: colors.backgroundLight,
  },
  textArea: {
    minHeight: 80,
    paddingTop: spacing.sm,
  },
});
