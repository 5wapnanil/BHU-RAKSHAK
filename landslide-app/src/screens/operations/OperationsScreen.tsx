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
import { Card } from '../../components';
import { colors } from '../../theme/colors';
import { typography, spacing, borderRadius } from '../../theme';
import { shadows } from '../../theme/shadows';
import { useLanguage, type TranslationKey } from '../../i18n';

interface OperationsScreenProps {
  navigation: any;
}

const OPERATION_ITEMS = [
  {
    key: 'Assignments',
    titleKey: 'operations.assignments.title' as TranslationKey,
    subtitleKey: 'operations.assignments.subtitle' as TranslationKey,
    icon: 'clipboard-outline' as const,
    bgColor: '#E3F2FD',
    iconColor: '#2196F3',
  },
  {
    key: 'ReliefResources',
    titleKey: 'operations.resources.title' as TranslationKey,
    subtitleKey: 'operations.resources.subtitle' as TranslationKey,
    icon: 'medical-outline' as const,
    bgColor: '#E8F5E9',
    iconColor: '#4CAF50',
  },
  {
    key: 'Shelters',
    titleKey: 'operations.shelters.title' as TranslationKey,
    subtitleKey: 'operations.shelters.subtitle' as TranslationKey,
    icon: 'home-outline' as const,
    bgColor: '#FFF3E0',
    iconColor: '#FF9800',
  },
];

export function OperationsScreen({ navigation }: OperationsScreenProps) {
  const { t } = useLanguage();
  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        <View style={styles.header}>
          <Text style={styles.headerTitle}>{t('operations.title')}</Text>
          <Text style={styles.headerSubtitle}>
            {t('operations.subtitle')}
          </Text>
        </View>

        <View style={styles.cardsContainer}>
          {OPERATION_ITEMS.map((item) => (
            <TouchableOpacity
              key={item.key}
              style={[styles.card, shadows.low]}
              onPress={() => navigation.navigate(item.key)}
              activeOpacity={0.7}
            >
              <View style={[styles.iconWrap, { backgroundColor: item.iconColor + '18' }]}>
                <Ionicons name={item.icon} size={32} color={item.iconColor} />
              </View>
              <View style={styles.cardContent}>
                <Text style={styles.cardTitle}>{t(item.titleKey)}</Text>
                <Text style={styles.cardSubtitle}>{t(item.subtitleKey)}</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color={colors.textLight} />
            </TouchableOpacity>
          ))}
        </View>
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
  header: {
    paddingHorizontal: spacing.base,
    paddingTop: spacing.xl,
    paddingBottom: spacing.base,
  },
  headerTitle: {
    fontSize: typography.fontSize.xxl,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  headerSubtitle: {
    fontSize: typography.fontSize.md,
    color: colors.textSecondary,
    lineHeight: 20,
  },
  cardsContainer: {
    paddingHorizontal: spacing.base,
    gap: spacing.md,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
  },
  iconWrap: {
    width: 56,
    height: 56,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  cardContent: {
    flex: 1,
  },
  cardTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    marginBottom: spacing.xxs,
  },
  cardSubtitle: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    lineHeight: 18,
  },
});
