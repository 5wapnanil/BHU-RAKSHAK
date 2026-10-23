import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SearchBar, AlertCard, Card } from '../components';
import { colors } from '../theme/colors';
import { typography, spacing, borderRadius } from '../theme';
import { useLocationShare } from '../hooks/useLocationShare';
import { useLanguage } from '../i18n';
import type { EmergencyCircleContact } from '../constants/emergencyContacts';

interface HomeScreenProps {
  navigation: any;
}

const EMERGENCY_ACTIONS = [
  {
    key: 'CallForEvacuation',
    titleKey: 'home.callForEvacuation',
    icon: 'walk-outline' as const,
    bgColor: '#FFF0ED',
    iconColor: colors.primary,
  },
  {
    key: 'VolunteerForEvacuation',
    titleKey: 'home.volunteerForEvacuation',
    icon: 'people-outline' as const,
    bgColor: '#E8F5E9',
    iconColor: '#4CAF50',
  },
  {
    key: 'RequestRelief',
    titleKey: 'home.requestRelief',
    icon: 'nutrition-outline' as const,
    bgColor: '#FFF3E0',
    iconColor: '#FF9800',
  },
  {
    key: 'VolunteerForRelief',
    titleKey: 'home.volunteerForRelief',
    icon: 'heart-outline' as const,
    bgColor: '#E3F2FD',
    iconColor: '#2196F3',
  },
] as const;

export function HomeScreen({ navigation }: HomeScreenProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const { shareState, shareLocation } = useLocationShare();
  const [emergencyContacts, setEmergencyContacts] = useState<EmergencyCircleContact[]>([]);
  const { t } = useLanguage();

  useEffect(() => {
    AsyncStorage.getItem('@aidconnect_emergency_circle')
      .then((raw) => {
        if (raw) setEmergencyContacts(JSON.parse(raw));
      })
      .catch(() => {});
  }, []);

  const handleActionPress = (screenName: string) => {
    navigation.navigate(screenName);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        <View style={styles.headerRow}>
          <View style={styles.headerLeft}>
            <SearchBar
              value={searchQuery}
              onChangeText={setSearchQuery}
              placeholder={t('common.searchPlaceholder')}
            />
          </View>
          <TouchableOpacity
            style={styles.avatarButton}
            onPress={() => navigation.navigate('SettingsTab')}
          >
            <Ionicons name="person" size={20} color={colors.white} />
          </TouchableOpacity>
        </View>

        <View style={styles.helpCard}>
          <View style={styles.helpCardContent}>
            <Text style={styles.helpTitle}>{t('home.needHelpTitle')}</Text>
            <Text style={styles.helpSubtitle}>
              {t('home.needHelpSubtitle')}
            </Text>
          </View>
          <TouchableOpacity
            style={styles.helpIcon}
            onPress={() => navigation.navigate('RequestRelief')}
          >
            <Ionicons name="ellipsis-horizontal" size={28} color={colors.primary} />
          </TouchableOpacity>
        </View>

        <Text style={styles.greeting}>{t('home.greeting')}</Text>
        <Text style={styles.greetingSub}>
          {t('home.greetingSub')}
        </Text>

        <View style={styles.actionsSection}>
          <Text style={styles.sectionLabel}>{t('home.quickActions')}</Text>
          <View style={styles.actionsGrid}>
            {EMERGENCY_ACTIONS.map((action) => (
              <TouchableOpacity
                key={action.key}
                style={[styles.actionCard, { backgroundColor: action.bgColor }]}
                onPress={() => handleActionPress(action.key)}
                activeOpacity={0.7}
              >
                <View style={[styles.actionIconWrap, { backgroundColor: action.iconColor + '18' }]}>
                  <Ionicons name={action.icon} size={28} color={action.iconColor} />
                </View>
                <Text style={styles.actionTitle}>{t(action.titleKey)}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <TouchableOpacity
          style={styles.fieldReportCard}
          activeOpacity={0.7}
          onPress={() => navigation.navigate('FieldReport')}
        >
          <View style={styles.fieldReportIconWrap}>
            <Ionicons name="camera" size={22} color={colors.white} />
          </View>
          <View style={styles.fieldReportContent}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
              <Text style={styles.fieldReportTitle}>Report Landslide Hazard</Text>
              <View style={styles.fieldReportTag}>
                <Text style={styles.fieldReportTagText}>FIELD INTEL</Text>
              </View>
            </View>
            <Text style={styles.fieldReportSubtitle}>
              Submit geotagged observations & photos to the central intelligence network.
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color={colors.textLight} />
        </TouchableOpacity>

        <AlertCard
          severity="high"
          title={t('home.heavyRainExpected')}
          location={t('home.baramulla')}
          time={t('home.minutesAgo')}
        />

        <TouchableOpacity
          style={styles.safetyGuideCard}
          activeOpacity={0.7}
          onPress={() => navigation.navigate('LandslideSafetyGuide')}
        >
          <View style={styles.safetyGuideIconWrap}>
            <Ionicons name="shield-half-outline" size={22} color={colors.primary} />
          </View>
          <View style={styles.safetyGuideContent}>
            <Text style={styles.safetyGuideTitle}>{t('home.safetyGuideTitle')}</Text>
            <Text style={styles.safetyGuideSubtitle}>
              {t('home.safetyGuideSubtitle')}
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color={colors.textLight} />
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.safetyGuideCard}
          activeOpacity={0.7}
          onPress={() => navigation.navigate('Assistant')}
        >
          <View style={[styles.safetyGuideIconWrap, { backgroundColor: '#FFF0ED' }]}>
            <Ionicons name="sparkles" size={22} color={colors.primary} />
          </View>
          <View style={styles.safetyGuideContent}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
              <Text style={styles.safetyGuideTitle}>{t('home.assistantTitle')}</Text>
              <View style={styles.fieldReportTag}>
                <Text style={styles.fieldReportTagText}>AI INTEL</Text>
              </View>
            </View>
            <Text style={styles.safetyGuideSubtitle}>
              {t('home.assistantSubtitle')}
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color={colors.textLight} />
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.shareLocationCard}
          activeOpacity={0.7}
          onPress={shareLocation}
          disabled={shareState === 'getting_location' || shareState === 'sharing'}
        >
          <View style={styles.shareLocationIconWrap}>
            {shareState === 'getting_location' || shareState === 'sharing' ? (
              <ActivityIndicator size={18} color={colors.primary} />
            ) : (
              <Ionicons name="share-social-outline" size={22} color={colors.primary} />
            )}
          </View>
          <View style={styles.shareLocationContent}>
            <Text style={styles.shareLocationTitle}>
              {shareState === 'getting_location' ? t('common.gettingLocation') : t('home.shareLocationTitle')}
            </Text>
            <Text style={styles.shareLocationSubtitle}>
              {t('home.shareLocationSubtitle')}
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color={colors.textLight} />
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.shelterCard}
          activeOpacity={0.7}
          onPress={() => navigation.navigate('NearbyShelters')}
        >
          <View style={styles.shelterIconWrap}>
            <Ionicons name="home-outline" size={22} color={colors.primary} />
          </View>
          <View style={styles.shelterContent}>
            <Text style={styles.shelterTitle}>{t('home.shelterTitle')}</Text>
            <Text style={styles.shelterSubtitle}>
              {t('home.shelterSubtitle')}
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color={colors.textLight} />
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.checkInCard}
          activeOpacity={0.7}
          onPress={() => navigation.navigate('PostDisasterCheckIn')}
        >
          <View style={styles.checkInIconWrap}>
            <Ionicons name="chatbubble-ellipses-outline" size={22} color={colors.primary} />
          </View>
          <View style={styles.checkInContent}>
            <Text style={styles.checkInTitle}>{t('home.checkInTitle')}</Text>
            <Text style={styles.checkInSubtitle}>
              {t('home.checkInSubtitle')}
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color={colors.textLight} />
        </TouchableOpacity>

        <View style={styles.emergencyCircleSection}>
          <View style={styles.emergencyCircleHeader}>
            <View style={styles.emergencyCircleTitleRow}>
              <Ionicons name="people" size={18} color={colors.primary} />
              <Text style={styles.emergencyCircleTitle}>{t('home.emergencyCircle')}</Text>
            </View>
            <TouchableOpacity
              activeOpacity={0.7}
              onPress={() => navigation.navigate('ContactTab')}
            >
              <Text style={styles.emergencyCircleViewAll}>{t('home.viewAll')}</Text>
            </TouchableOpacity>
          </View>

          {emergencyContacts.length === 0 ? (
            <View style={styles.emergencyCircleEmpty}>
              <Text style={styles.emergencyCircleEmptyText}>
                {t('home.addTrustedContact')}
              </Text>
              <TouchableOpacity
                style={styles.emergencyCircleAddBtn}
                activeOpacity={0.7}
                onPress={() => navigation.navigate('ContactTab')}
              >
                <Ionicons name="add-circle-outline" size={16} color={colors.primary} />
                <Text style={styles.emergencyCircleAddText}>{t('home.addContact')}</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <>
              {emergencyContacts.slice(0, 3).map((contact) => (
                <View key={contact.id} style={styles.emergencyCircleItem}>
                  <View style={styles.emergencyCircleItemLeft}>
                    <View style={styles.emergencyCircleAvatar}>
                      <Ionicons name="person" size={14} color={colors.white} />
                    </View>
                    <View style={styles.emergencyCircleItemInfo}>
                      <Text style={styles.emergencyCircleItemName}>{contact.name}</Text>
                      <Text style={styles.emergencyCircleItemRel}>{contact.relationship}</Text>
                    </View>
                  </View>
                  <TouchableOpacity
                    style={styles.emergencyCircleCallBtn}
                    activeOpacity={0.7}
                    onPress={() => {
                      const url = `tel:${contact.phone}`;
                      Linking.canOpenURL(url).then((s) => s && Linking.openURL(url));
                    }}
                  >
                    <Ionicons name="call" size={14} color={colors.white} />
                  </TouchableOpacity>
                </View>
              ))}
              {emergencyContacts.length > 3 && (
                <TouchableOpacity
                  style={styles.emergencyCircleMore}
                  activeOpacity={0.7}
                  onPress={() => navigation.navigate('ContactTab')}
                >
                  <Text style={styles.emergencyCircleMoreText}>
                    {t('home.moreCount', { count: emergencyContacts.length - 3 })}
                  </Text>
                </TouchableOpacity>
              )}
            </>
          )}
        </View>

        <View style={styles.weatherRow}>
          <WeatherChip icon="thermometer-outline" value="23.3°" />
          <WeatherChip icon="water-outline" value="54%" />
          <WeatherChip icon="rainy-outline" value="88%" />
          <WeatherChip icon="compass-outline" value="NW" />
        </View>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>{t('home.weatherUpdates')}</Text>
          <TouchableOpacity>
            <Text style={styles.seeMore}>{t('home.seeMore')}</Text>
          </TouchableOpacity>
        </View>

        <Card style={styles.newsCard}>
          <View style={styles.newsContent}>
            <Text style={styles.newsTitle}>
              {t('home.weatherNewsTitle')}
            </Text>
            <Text style={styles.newsSource}>{t('home.weatherNewsSource')}</Text>
          </View>
          <View style={styles.newsImagePlaceholder}>
            <Ionicons name="image-outline" size={32} color={colors.textLight} />
          </View>
        </Card>

        <View style={{ height: 20 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

function WeatherChip({ icon, value }: { icon: string; value: string }) {
  return (
    <View style={styles.weatherChip}>
      <Ionicons name={icon as any} size={18} color={colors.textSecondary} />
      <Text style={styles.weatherChipValue}>{value}</Text>
    </View>
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
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingRight: spacing.base,
    paddingTop: spacing.xl,
  },
  headerLeft: {
    flex: 1,
  },
  avatarButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: spacing.sm,
  },
  helpCard: {
    flexDirection: 'row',
    backgroundColor: colors.primary,
    marginHorizontal: spacing.base,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    marginTop: spacing.sm,
    alignItems: 'center',
  },
  helpCardContent: {
    flex: 1,
  },
  helpTitle: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.white,
    marginBottom: spacing.xs,
  },
  helpSubtitle: {
    fontSize: typography.fontSize.sm,
    color: colors.white,
    opacity: 0.9,
    lineHeight: 18,
  },
  helpIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.white,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: spacing.md,
  },
  greeting: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    marginHorizontal: spacing.base,
    marginTop: spacing.xl,
  },
  greetingSub: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginHorizontal: spacing.base,
    marginTop: spacing.xs,
    lineHeight: 20,
    marginBottom: spacing.base,
  },
  actionsSection: {
    marginHorizontal: spacing.base,
    marginBottom: spacing.base,
  },
  sectionLabel: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    marginBottom: spacing.md,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  actionCard: {
    width: '48%' as any,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    minHeight: 110,
    justifyContent: 'flex-start',
  },
  actionIconWrap: {
    width: 48,
    height: 48,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  actionTitle: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    lineHeight: 20,
  },
  weatherRow: {
    flexDirection: 'row',
    marginHorizontal: spacing.base,
    gap: spacing.sm,
    marginTop: spacing.md,
    marginBottom: spacing.base,
  },
  weatherChip: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.white,
    borderRadius: borderRadius.md,
    paddingVertical: spacing.sm,
    gap: spacing.xs,
  },
  weatherChipValue: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginHorizontal: spacing.base,
    marginTop: spacing.sm,
    marginBottom: spacing.sm,
  },
  sectionTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
  },
  seeMore: {
    fontSize: typography.fontSize.sm,
    color: colors.primary,
    fontWeight: typography.fontWeight.semiBold,
  },
  newsCard: {
    flexDirection: 'row',
    marginHorizontal: spacing.base,
    alignItems: 'center',
  },
  newsContent: {
    flex: 1,
    marginRight: spacing.md,
  },
  newsTitle: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    lineHeight: 20,
    marginBottom: spacing.xs,
  },
  newsSource: {
    fontSize: typography.fontSize.xs,
    color: colors.textLight,
  },
  newsImagePlaceholder: {
    width: 80,
    height: 80,
    borderRadius: borderRadius.md,
    backgroundColor: colors.backgroundGray,
    alignItems: 'center',
    justifyContent: 'center',
  },
  fieldReportCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.white,
    marginHorizontal: spacing.base,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    marginBottom: spacing.base,
    borderWidth: 1.5,
    borderColor: '#E8654A33',
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 2,
  },
  fieldReportIconWrap: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.md,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  fieldReportContent: {
    flex: 1,
  },
  fieldReportTitle: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
  },
  fieldReportTag: {
    backgroundColor: '#FFF0ED',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  fieldReportTagText: {
    fontSize: 9,
    fontWeight: '700',
    color: colors.primary,
  },
  fieldReportSubtitle: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
    lineHeight: 16,
    marginTop: 2,
  },
  safetyGuideCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.white,
    marginHorizontal: spacing.base,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    marginBottom: spacing.base,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  safetyGuideIconWrap: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.md,
    backgroundColor: '#FDE8E4',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  safetyGuideContent: {
    flex: 1,
  },
  safetyGuideTitle: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  safetyGuideSubtitle: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginTop: 2,
  },
  shareLocationCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.white,
    marginHorizontal: spacing.base,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    marginBottom: spacing.base,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  shareLocationIconWrap: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.md,
    backgroundColor: '#E3F2FD',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  shareLocationContent: {
    flex: 1,
  },
  shareLocationTitle: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  shareLocationSubtitle: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginTop: 2,
  },
  shelterCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.white,
    marginHorizontal: spacing.base,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    marginBottom: spacing.base,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  shelterIconWrap: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.md,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  shelterContent: {
    flex: 1,
  },
  shelterTitle: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  shelterSubtitle: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginTop: 2,
  },
  checkInCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.white,
    marginHorizontal: spacing.base,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    marginBottom: spacing.base,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  checkInIconWrap: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.md,
    backgroundColor: '#FDE8E4',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  checkInContent: {
    flex: 1,
  },
  checkInTitle: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  checkInSubtitle: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginTop: 2,
  },
  emergencyCircleSection: {
    backgroundColor: colors.white,
    marginHorizontal: spacing.base,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    marginBottom: spacing.base,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  emergencyCircleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  emergencyCircleTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  emergencyCircleTitle: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  emergencyCircleViewAll: {
    fontSize: typography.fontSize.sm,
    color: colors.primary,
    fontWeight: typography.fontWeight.semiBold,
  },
  emergencyCircleEmpty: {
    alignItems: 'center',
    paddingVertical: spacing.md,
  },
  emergencyCircleEmptyText: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  emergencyCircleAddBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
    borderWidth: 1.5,
    borderColor: colors.primary,
    borderStyle: 'dashed',
  },
  emergencyCircleAddText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.primary,
  },
  emergencyCircleItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.borderLight,
  },
  emergencyCircleItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    flex: 1,
  },
  emergencyCircleAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emergencyCircleItemInfo: {
    flex: 1,
  },
  emergencyCircleItemName: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  emergencyCircleItemRel: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
  },
  emergencyCircleCallBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.success,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emergencyCircleMore: {
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.borderLight,
  },
  emergencyCircleMoreText: {
    fontSize: typography.fontSize.sm,
    color: colors.primary,
    fontWeight: typography.fontWeight.medium,
  },
});
