import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { typography, spacing, borderRadius } from '../theme';
import { useLanguage, type TranslationKey } from '../i18n';

interface Props {
  navigation: any;
}

interface Bullet {
  textKey: TranslationKey;
  icon?: keyof typeof Ionicons.glyphMap;
  iconColor?: string;
}

interface Section {
  headingKey: TranslationKey;
  icon: keyof typeof Ionicons.glyphMap;
  iconColor: string;
  bgColor: string;
  bullets: Bullet[];
}

const SECTIONS: Section[] = [
  {
    headingKey: 'safetyGuide.sections.before',
    icon: 'shield-checkmark-outline',
    iconColor: colors.primary,
    bgColor: '#FFF0ED',
    bullets: [
      { textKey: 'safetyGuide.bullets.before.0' },
      { textKey: 'safetyGuide.bullets.before.1' },
      { textKey: 'safetyGuide.bullets.before.2' },
      { textKey: 'safetyGuide.bullets.before.3' },
      { textKey: 'safetyGuide.bullets.before.4' },
      { textKey: 'safetyGuide.bullets.before.5' },
    ],
  },
  {
    headingKey: 'safetyGuide.sections.during',
    icon: 'warning-outline',
    iconColor: '#FF9800',
    bgColor: '#FFF3E0',
    bullets: [
      { textKey: 'safetyGuide.bullets.during.0' },
      { textKey: 'safetyGuide.bullets.during.1' },
      { textKey: 'safetyGuide.bullets.during.2' },
      { textKey: 'safetyGuide.bullets.during.3' },
      { textKey: 'safetyGuide.bullets.during.4' },
      { textKey: 'safetyGuide.bullets.during.5', icon: 'call-outline', iconColor: colors.primary },
    ],
  },
  {
    headingKey: 'safetyGuide.sections.onRoad',
    icon: 'car-outline',
    iconColor: '#2196F3',
    bgColor: '#E3F2FD',
    bullets: [
      { textKey: 'safetyGuide.bullets.onRoad.0' },
      { textKey: 'safetyGuide.bullets.onRoad.1' },
      { textKey: 'safetyGuide.bullets.onRoad.2' },
      { textKey: 'safetyGuide.bullets.onRoad.3' },
      { textKey: 'safetyGuide.bullets.onRoad.4' },
    ],
  },
  {
    headingKey: 'safetyGuide.sections.trapped',
    icon: 'alert-circle-outline',
    iconColor: '#D32F2F',
    bgColor: '#FFEBEE',
    bullets: [
      { textKey: 'safetyGuide.bullets.trapped.0' },
      { textKey: 'safetyGuide.bullets.trapped.1' },
      { textKey: 'safetyGuide.bullets.trapped.2', icon: 'call-outline', iconColor: '#D32F2F' },
      { textKey: 'safetyGuide.bullets.trapped.3' },
      { textKey: 'safetyGuide.bullets.trapped.4' },
      { textKey: 'safetyGuide.bullets.trapped.5' },
      { textKey: 'safetyGuide.bullets.trapped.6' },
      { textKey: 'safetyGuide.bullets.trapped.7' },
    ],
  },
  {
    headingKey: 'safetyGuide.sections.after',
    icon: 'checkmark-circle-outline',
    iconColor: '#4CAF50',
    bgColor: '#E8F5E9',
    bullets: [
      { textKey: 'safetyGuide.bullets.after.0' },
      { textKey: 'safetyGuide.bullets.after.1' },
      { textKey: 'safetyGuide.bullets.after.2' },
      { textKey: 'safetyGuide.bullets.after.3' },
      { textKey: 'safetyGuide.bullets.after.4' },
      { textKey: 'safetyGuide.bullets.after.5' },
    ],
  },
];

function SectionBlock({ section, t }: { section: Section; t: (key: TranslationKey) => string }) {
  return (
    <View style={styles.section}>
      <View style={[styles.sectionHeader, { backgroundColor: section.bgColor }]}>
        <View style={[styles.sectionIconWrap, { backgroundColor: section.iconColor + '18' }]}>
          <Ionicons name={section.icon} size={20} color={section.iconColor} />
        </View>
        <Text style={[styles.sectionHeading, { color: section.iconColor }]}>
          {t(section.headingKey)}
        </Text>
      </View>
      <View style={styles.bulletList}>
        {section.bullets.map((bullet, i) => (
          <View key={i} style={styles.bulletRow}>
            <Ionicons
              name={bullet.icon || 'ellipse'}
              size={bullet.icon ? 14 : 5}
              color={bullet.iconColor || colors.textLight}
              style={styles.bulletDot}
            />
            <Text style={styles.bulletText}>{t(bullet.textKey)}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

export function LandslideSafetyGuideScreen({ navigation }: Props) {
  const { t } = useLanguage();
  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={22} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('safetyGuide.title')}</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        <View style={styles.heroSection}>
          <View style={styles.heroIconWrap}>
            <Ionicons name="shield-half-outline" size={32} color={colors.primary} />
          </View>
          <Text style={styles.heroTitle}>{t('safetyGuide.heroTitle')}</Text>
          <Text style={styles.heroSubtitle}>
            {t('safetyGuide.heroSubtitle')}
          </Text>
        </View>

        {SECTIONS.map((section, i) => (
          <SectionBlock key={i} section={section} t={t} />
        ))}

        <View style={styles.divider} />

        <View style={styles.helpSection}>
          <Text style={styles.helpHeading}>{t('safetyGuide.needHelp')}</Text>
          <Text style={styles.helpSubtext}>
            {t('safetyGuide.needHelpSubtext')}
          </Text>

          <TouchableOpacity
            style={styles.actionButton}
            activeOpacity={0.7}
            onPress={() => navigation.navigate('EmergencyCenter')}
          >
            <View style={[styles.actionIconWrap, { backgroundColor: '#FDE8E4' }]}>
              <Ionicons name="shield" size={22} color={colors.primary} />
            </View>
            <View style={styles.actionContent}>
              <Text style={styles.actionLabel}>{t('common.sos')}</Text>
              <Text style={styles.actionDesc}>{t('safetyGuide.sosDesc')}</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={colors.textLight} />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            activeOpacity={0.7}
            onPress={() => navigation.navigate('RequestRelief')}
          >
            <View style={[styles.actionIconWrap, { backgroundColor: '#FFF3E0' }]}>
              <Ionicons name="hand-left-outline" size={22} color="#FF9800" />
            </View>
            <View style={styles.actionContent}>
              <Text style={styles.actionLabel}>{t('safetyGuide.requestHelp')}</Text>
              <Text style={styles.actionDesc}>{t('safetyGuide.requestHelpDesc')}</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={colors.textLight} />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            activeOpacity={0.7}
            onPress={() => navigation.navigate('ContactTab')}
          >
            <View style={[styles.actionIconWrap, { backgroundColor: '#E3F2FD' }]}>
              <Ionicons name="people" size={22} color="#2196F3" />
            </View>
            <View style={styles.actionContent}>
              <Text style={styles.actionLabel}>{t('safetyGuide.emergencyContacts')}</Text>
              <Text style={styles.actionDesc}>{t('safetyGuide.emergencyContactsDesc')}</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={colors.textLight} />
          </TouchableOpacity>
        </View>

        <View style={styles.footer}>
          <Ionicons name="information-circle-outline" size={14} color={colors.textLight} />
          <Text style={styles.footerText}>
            {t('safetyGuide.footerText')}
          </Text>
        </View>

        <Text style={styles.footerEmergency}>{t('safetyGuide.emergency')}</Text>

        <View style={{ height: 20 }} />
      </ScrollView>
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
  backButton: {
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
  scrollContent: {
    paddingBottom: 20,
  },
  heroSection: {
    alignItems: 'center',
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.lg,
  },
  heroIconWrap: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#FDE8E4',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  heroTitle: {
    fontSize: typography.fontSize.xxl,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    textAlign: 'center',
    marginBottom: spacing.xs,
  },
  heroSubtitle: {
    fontSize: typography.fontSize.md,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
  section: {
    marginHorizontal: spacing.base,
    marginBottom: spacing.lg,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  sectionIconWrap: {
    width: 32,
    height: 32,
    borderRadius: borderRadius.sm,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.sm,
  },
  sectionHeading: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.bold,
  },
  bulletList: {
    paddingLeft: spacing.xs,
  },
  bulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
    paddingRight: spacing.sm,
  },
  bulletDot: {
    marginTop: 6,
    marginRight: spacing.sm,
    minWidth: 14,
  },
  bulletText: {
    flex: 1,
    fontSize: typography.fontSize.md,
    color: colors.text,
    lineHeight: 22,
  },
  divider: {
    height: 1,
    backgroundColor: colors.borderLight,
    marginHorizontal: spacing.base,
    marginVertical: spacing.lg,
  },
  helpSection: {
    marginHorizontal: spacing.base,
    marginBottom: spacing.lg,
  },
  helpHeading: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  helpSubtext: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginBottom: spacing.base,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  actionIconWrap: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  actionContent: {
    flex: 1,
  },
  actionLabel: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  actionDesc: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginTop: 2,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginHorizontal: spacing.base,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    backgroundColor: colors.white,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.borderLight,
    gap: spacing.sm,
  },
  footerText: {
    flex: 1,
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    lineHeight: 20,
  },
  footerEmergency: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.primary,
    textAlign: 'center',
    marginTop: spacing.md,
  },
});
