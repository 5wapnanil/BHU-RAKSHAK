import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ViewStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { spacing, typography } from '../theme';

interface AppHeaderProps {
  title?: string;
  subtitle?: string;
  greeting?: string;
  showAvatar?: boolean;
  avatarUrl?: string;
  showBack?: boolean;
  onBackPress?: () => void;
  rightIcon?: keyof typeof Ionicons.glyphMap;
  onRightIconPress?: () => void;
  variant?: 'default' | 'gradient' | 'compact';
  style?: ViewStyle;
}

export function AppHeader({
  title,
  subtitle,
  greeting,
  showAvatar = false,
  showBack = false,
  onBackPress,
  rightIcon,
  onRightIconPress,
  variant = 'default',
  style,
}: AppHeaderProps) {
  return (
    <View style={[styles.container, variant === 'gradient' && styles.gradientContainer, style]}>
      <View style={styles.row}>
        <View style={styles.left}>
          {showBack && (
            <TouchableOpacity onPress={onBackPress} style={styles.backButton}>
              <Ionicons name="arrow-back" size={24} color={colors.text} />
            </TouchableOpacity>
          )}
          <View style={styles.textContainer}>
            {greeting && <Text style={styles.greeting}>{greeting}</Text>}
            {title && <Text style={styles.title}>{title}</Text>}
            {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
          </View>
        </View>
        <View style={styles.right}>
          {rightIcon && (
            <TouchableOpacity onPress={onRightIconPress} style={styles.iconButton}>
              <Ionicons name={rightIcon} size={24} color={colors.text} />
            </TouchableOpacity>
          )}
          {showAvatar && (
            <View style={styles.avatar}>
              <Ionicons name="person" size={20} color={colors.white} />
            </View>
          )}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: spacing.base,
    paddingTop: spacing.xl,
    paddingBottom: spacing.md,
  },
  gradientContainer: {
    backgroundColor: colors.primary,
    paddingTop: spacing.xxxl,
    paddingBottom: spacing.xxl,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  left: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  right: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  backButton: {
    marginRight: spacing.sm,
    padding: spacing.xs,
  },
  textContainer: {
    flex: 1,
  },
  greeting: {
    fontSize: typography.fontSize.base,
    color: colors.textSecondary,
    fontWeight: typography.fontWeight.regular,
  },
  title: {
    fontSize: typography.fontSize.xxl,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
  },
  subtitle: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    marginTop: spacing.xxs,
  },
  iconButton: {
    padding: spacing.xs,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
