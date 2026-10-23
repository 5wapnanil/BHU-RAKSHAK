import React, { useState } from 'react';
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
import { InputField, AppButton, Card } from '../components';
import { colors } from '../theme/colors';
import { typography, spacing, borderRadius } from '../theme';
import { useLanguage, LANGUAGES } from '../i18n';

interface ProfileLoginScreenProps {
  navigation: any;
}

type ViewMode = 'login' | 'register' | 'profile';

const MOCK_PROFILE = {
  name: 'Ravik Kumar',
  email: 'ravik@example.com',
  phone: '+91 98765 43210',
  memberSince: 'January 2024',
  requestsMade: 6,
  volunteerHours: 12,
  area: 'Srinagar, J&K',
};

export function ProfileLoginScreen({ navigation }: ProfileLoginScreenProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { language, setLanguage, t } = useLanguage();

  const handleSignIn = () => {
    if (!email.trim()) {
      Alert.alert(t('profile.requiredTitle'), t('profile.enterEmail'));
      return;
    }
    if (!password.trim()) {
      Alert.alert(t('profile.requiredTitle'), t('profile.enterPassword'));
      return;
    }
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setViewMode('profile');
    }, 1200);
  };

  const handleSignUp = () => {
    if (!name.trim()) {
      Alert.alert(t('profile.requiredTitle'), t('profile.enterName'));
      return;
    }
    if (!email.trim()) {
      Alert.alert(t('profile.requiredTitle'), t('profile.enterEmail'));
      return;
    }
    if (!password.trim()) {
      Alert.alert(t('profile.requiredTitle'), t('profile.enterPassword'));
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert(t('profile.errorTitle'), t('profile.passwordMismatch'));
      return;
    }
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setViewMode('profile');
    }, 1200);
  };

  const handleSignOut = () => {
    Alert.alert(t('profile.signOut'), t('profile.signOutConfirm'), [
      { text: t('common.cancel'), style: 'cancel' },
      {
        text: t('profile.signOut'),
        style: 'destructive',
        onPress: () => {
          setEmail('');
          setPassword('');
          setName('');
          setConfirmPassword('');
          setViewMode('login');
        },
      },
    ]);
  };

  if (viewMode === 'profile') {
    return (
      <View style={styles.container}>
        <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
          <View style={styles.profileHeader}>
            <View style={styles.avatarLarge}>
              <Ionicons name="person" size={40} color={colors.white} />
            </View>
            <Text style={styles.profileName}>{MOCK_PROFILE.name}</Text>
            <Text style={styles.profileEmail}>{MOCK_PROFILE.email}</Text>
          </View>

          <Card style={styles.statsCard}>
            <View style={styles.statsRow}>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>{MOCK_PROFILE.requestsMade}</Text>
                <Text style={styles.statLabel}>{t('profile.requests')}</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>{MOCK_PROFILE.volunteerHours}</Text>
                <Text style={styles.statLabel}>{t('profile.volHours')}</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <Ionicons name="location" size={16} color={colors.primary} />
                <Text style={styles.statArea}>{MOCK_PROFILE.area}</Text>
              </View>
            </View>
          </Card>

          <View style={styles.menuSection}>
            <Text style={styles.menuSectionTitle}>{t('profile.account')}</Text>
            <Card style={styles.menuCard}>
              <MenuItem icon="person-outline" label={t('profile.editProfile')} />
              <MenuItem icon="call-outline" label={t('profile.phone')} value={MOCK_PROFILE.phone} />
              <MenuItem icon="mail-outline" label={t('profile.email')} value={MOCK_PROFILE.email} />
              <MenuItem icon="calendar-outline" label={t('profile.memberSince')} value={MOCK_PROFILE.memberSince} last />
            </Card>
          </View>

          <View style={styles.menuSection}>
            <Text style={styles.menuSectionTitle}>{t('common.language')}</Text>
            <Card style={styles.menuCard}>
              {LANGUAGES.map((lang, index) => {
                const isActive = language === lang.key;
                return (
                  <TouchableOpacity
                    key={lang.key}
                    style={[
                      styles.menuItem,
                      index < LANGUAGES.length - 1 && styles.menuItemBorder,
                    ]}
                    activeOpacity={0.6}
                    onPress={() => setLanguage(lang.key)}
                  >
                    <Ionicons
                      name={isActive ? 'radio-button-on' : 'radio-button-off'}
                      size={20}
                      color={isActive ? colors.primary : colors.textSecondary}
                    />
                    <Text
                      style={[
                        styles.menuItemLabel,
                        isActive && styles.languageLabelActive,
                      ]}
                    >
                      {lang.key === 'en' ? t('common.english') : t('common.hindi')}
                    </Text>
                    {isActive && (
                      <Ionicons name="checkmark-circle" size={18} color={colors.primary} />
                    )}
                  </TouchableOpacity>
                );
              })}
            </Card>
          </View>

          <View style={styles.menuSection}>
            <Text style={styles.menuSectionTitle}>{t('profile.activity')}</Text>
            <Card style={styles.menuCard}>
              <MenuItem icon="document-text-outline" label={t('profile.myRequests')} />
              <MenuItem icon="heart-outline" label={t('profile.volunteerHistory')} />
              <MenuItem icon="notifications-outline" label={t('profile.notificationSettings')} last />
            </Card>
          </View>

          <View style={styles.menuSection}>
            <Text style={styles.menuSectionTitle}>{t('profile.support')}</Text>
            <Card style={styles.menuCard}>
              <MenuItem icon="help-circle-outline" label={t('profile.helpFaq')} />
              <MenuItem icon="chatbubble-outline" label={t('profile.contactSupport')} />
              <MenuItem icon="document-outline" label={t('profile.terms')} last />
            </Card>
          </View>

          <AppButton
            title={t('profile.signOut')}
            variant="outline"
            onPress={handleSignOut}
            style={styles.signOutBtn}
          />

          <View style={styles.loginPrompt}>
            <Text style={styles.loginPromptText}>
              {t('profile.emergencyAvailable')}
            </Text>
          </View>
        </ScrollView>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        <View style={styles.decorativeBlob} />
        <View style={styles.decorativeBlob2} />

        <Text style={styles.welcomeText}>
          {viewMode === 'register' ? t('profile.welcome') : t('profile.welcomeBack')}
        </Text>
        <Text style={styles.appName}>{t('profile.appName')}</Text>
        <Text style={styles.authSubtitle}>
          {viewMode === 'register'
            ? t('profile.authSubtitleRegister')
            : t('profile.authSubtitleLogin')}
        </Text>

        <View style={styles.formContainer}>
          {viewMode === 'register' && (
            <InputField
              icon="person-outline"
              placeholder={t('profile.namePlaceholder')}
              value={name}
              onChangeText={setName}
            />
          )}

          <InputField
            icon="mail-outline"
            placeholder={t('profile.emailPlaceholder')}
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
          />

          <InputField
            icon="lock-closed-outline"
            placeholder={t('profile.passwordPlaceholder')}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />

          {viewMode === 'register' && (
            <InputField
              icon="lock-closed-outline"
              placeholder={t('profile.confirmPasswordPlaceholder')}
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              secureTextEntry
            />
          )}

          <AppButton
            title={viewMode === 'register' ? t('common.signUp') : t('common.signIn')}
            onPress={viewMode === 'register' ? handleSignUp : handleSignIn}
            loading={loading}
            style={styles.submitBtn}
          />

          <Text style={styles.dividerText}>
            {viewMode === 'register' ? t('profile.orSignUp') : t('profile.orSignIn')}
          </Text>

          <View style={styles.socialRow}>
            <TouchableOpacity style={styles.socialButton}>
              <Ionicons name="logo-google" size={24} color={colors.text} />
            </TouchableOpacity>
            <TouchableOpacity style={styles.socialButton}>
              <Ionicons name="logo-apple" size={24} color={colors.text} />
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={styles.switchMode}
            onPress={() => setViewMode(viewMode === 'register' ? 'login' : 'register')}
          >
            <Text style={styles.switchText}>
              {viewMode === 'register' ? t('profile.haveAccount') : t('profile.noAccount')}
            </Text>
            <Text style={styles.switchLink}>
              {viewMode === 'register' ? t('profile.signInLink') : t('profile.signUpLink')}
            </Text>
          </TouchableOpacity>

          <View style={styles.skipContainer}>
            <TouchableOpacity
              style={styles.skipButton}
              onPress={() => setViewMode('profile')}
            >
              <Text style={styles.skipText}>{t('profile.continueWithout')}</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.emergencyNote}>
            <Ionicons name="shield-checkmark-outline" size={16} color={colors.primary} />
            <Text style={styles.emergencyNoteText}>
              {t('profile.emergencyNote')}
            </Text>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function MenuItem({
  icon,
  label,
  value,
  last = false,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  value?: string;
  last?: boolean;
}) {
  return (
    <TouchableOpacity style={[styles.menuItem, !last && styles.menuItemBorder]} activeOpacity={0.6}>
      <Ionicons name={icon} size={20} color={colors.textSecondary} />
      <Text style={styles.menuItemLabel}>{label}</Text>
      {value && <Text style={styles.menuItemValue}>{value}</Text>}
      <Ionicons name="chevron-forward" size={16} color={colors.textLight} />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.white,
  },
  scrollContent: {
    paddingBottom: spacing.xxxl,
  },
  decorativeBlob: {
    position: 'absolute',
    top: -60,
    right: -40,
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: colors.primary,
    opacity: 0.1,
  },
  decorativeBlob2: {
    position: 'absolute',
    top: 20,
    right: 30,
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: colors.primary,
    opacity: 0.08,
  },
  welcomeText: {
    fontSize: typography.fontSize.xxl,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    marginTop: 80,
    marginHorizontal: spacing.xl,
  },
  appName: {
    fontSize: typography.fontSize.xxxl,
    fontWeight: typography.fontWeight.bold,
    color: colors.primary,
    marginHorizontal: spacing.xl,
    marginBottom: spacing.sm,
  },
  authSubtitle: {
    fontSize: typography.fontSize.md,
    color: colors.textSecondary,
    marginHorizontal: spacing.xl,
    marginBottom: spacing.xxl,
  },
  formContainer: {
    paddingHorizontal: spacing.xl,
  },
  submitBtn: {
    marginTop: spacing.md,
  },
  dividerText: {
    fontSize: typography.fontSize.sm,
    color: colors.textLight,
    textAlign: 'center',
    marginVertical: spacing.lg,
  },
  socialRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: spacing.xl,
    marginBottom: spacing.xxl,
  },
  socialButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  switchMode: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.base,
  },
  switchText: {
    fontSize: typography.fontSize.md,
    color: colors.textSecondary,
  },
  switchLink: {
    fontSize: typography.fontSize.md,
    color: colors.primary,
    fontWeight: typography.fontWeight.semiBold,
  },
  skipContainer: {
    alignItems: 'center',
    marginTop: spacing.md,
  },
  skipButton: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.base,
  },
  skipText: {
    fontSize: typography.fontSize.md,
    color: colors.textLight,
    textDecorationLine: 'underline',
  },
  emergencyNote: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.sosBackground,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginTop: spacing.xl,
  },
  emergencyNoteText: {
    flex: 1,
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    lineHeight: 18,
  },
  profileHeader: {
    alignItems: 'center',
    paddingTop: spacing.xxl + spacing.lg,
    paddingBottom: spacing.xl,
    backgroundColor: colors.white,
  },
  avatarLarge: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  profileName: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
  },
  profileEmail: {
    fontSize: typography.fontSize.md,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  statsCard: {
    marginHorizontal: spacing.base,
    marginTop: spacing.base,
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
    gap: spacing.xs,
  },
  statNumber: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.primary,
  },
  statLabel: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
  },
  statDivider: {
    width: 1,
    height: 36,
    backgroundColor: colors.borderLight,
  },
  statArea: {
    fontSize: typography.fontSize.xs,
    color: colors.primary,
    fontWeight: typography.fontWeight.medium,
  },
  menuSection: {
    marginTop: spacing.xl,
    paddingHorizontal: spacing.base,
  },
  menuSectionTitle: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
    marginLeft: spacing.xs,
  },
  menuCard: {
    padding: 0,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.base,
    gap: spacing.md,
  },
  menuItemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
  },
  menuItemLabel: {
    flex: 1,
    fontSize: typography.fontSize.md,
    color: colors.text,
  },
  menuItemValue: {
    fontSize: typography.fontSize.sm,
    color: colors.textLight,
    marginRight: spacing.xs,
  },
  languageLabelActive: {
    color: colors.primary,
    fontWeight: typography.fontWeight.semiBold,
  },
  signOutBtn: {
    marginHorizontal: spacing.base,
    marginTop: spacing.xxl,
  },
  loginPrompt: {
    alignItems: 'center',
    marginTop: spacing.base,
    paddingHorizontal: spacing.xl,
  },
  loginPromptText: {
    fontSize: typography.fontSize.sm,
    color: colors.textLight,
    textAlign: 'center',
  },
});
