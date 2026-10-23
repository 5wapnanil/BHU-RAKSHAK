import React, { useState, useRef, useCallback, useEffect } from 'react';
import { TouchableOpacity, Text, StyleSheet, View, ViewStyle, Animated, Easing, AppState, AppStateStatus } from 'react-native';
import { colors } from '../theme/colors';
import { borderRadius, spacing, typography } from '../theme';
import { useLanguage } from '../i18n';

export interface EmergencyButtonProps {
  onSOSActivated: () => void | boolean | Promise<void | boolean>;
  size?: number;
  style?: ViewStyle;
  disabled?: boolean;
}

const HOLD_DURATION = 3000;
const PROGRESS_UPDATE_INTERVAL = 50;

export function EmergencyButton({
  onSOSActivated,
  size = 160,
  style,
  disabled = false,
}: EmergencyButtonProps) {
  const { t } = useLanguage();
  const [holdProgress, setHoldProgress] = useState(0);
  const [holdText, setHoldText] = useState(t('sos.holdFor3'));
  const [isHolding, setIsHolding] = useState(false);
  const [triggered, setTriggered] = useState(false);

  const holdTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const progressTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const clearTimers = useCallback(() => {
    if (holdTimerRef.current) {
      clearTimeout(holdTimerRef.current);
      holdTimerRef.current = null;
    }
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
    }
  }, []);

  const resetState = useCallback(() => {
    if (!isMountedRef.current) return;
    setHoldProgress(0);
    setHoldText(t('sos.holdFor3'));
    setIsHolding(false);
    setTriggered(false);
    clearTimers();
  }, [clearTimers, t]);

  const handlePressIn = useCallback(() => {
    if (disabled || triggered) return;

    setIsHolding(true);
    setHoldProgress(0);
    setHoldText(t('sos.keepHolding'));
    startTimeRef.current = Date.now();

    holdTimerRef.current = setTimeout(async () => {
      setTriggered(true);
      setHoldText(t('sos.calling112'));
      clearTimers();
      try {
        const result = await onSOSActivated();
        if (result === false) {
          resetState();
        }
      } catch {
        resetState();
      }
    }, HOLD_DURATION);

    progressTimerRef.current = setInterval(() => {
      const elapsed = Date.now() - startTimeRef.current;
      const progress = Math.min(elapsed / HOLD_DURATION, 1);
      setHoldProgress(progress);
    }, PROGRESS_UPDATE_INTERVAL);
  }, [disabled, triggered, onSOSActivated, clearTimers, resetState, t]);

  const handlePressOut = useCallback(() => {
    if (!isHolding) return;
    clearTimers();
    if (!triggered) {
      resetState();
    }
  }, [isHolding, triggered, clearTimers, resetState]);

  useEffect(() => {
    return () => clearTimers();
  }, [clearTimers]);

  useEffect(() => {
    const handleAppStateChange = (nextState: AppStateStatus) => {
      if (nextState === 'active' && triggered) {
        resetState();
      }
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);
    return () => subscription.remove();
  }, [triggered, resetState]);

  const outerRingSize = size + 40;
  const middleRingSize = size + 20;

  const progressRingColor = isHolding
    ? `rgba(255, 255, 255, ${0.3 + holdProgress * 0.5})`
    : colors.sosRing;

  return (
    <TouchableOpacity
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      activeOpacity={0.9}
      disabled={disabled || triggered}
      style={[
        styles.outerContainer,
        { width: outerRingSize, height: outerRingSize },
        style,
      ]}
      accessibilityLabel={t('sos.accessibilityLabel')}
      accessibilityHint={t('sos.accessibilityHint')}
    >
      <View
        style={[
          styles.middleRing,
          { width: middleRingSize, height: middleRingSize, backgroundColor: progressRingColor },
        ]}
      >
        <View style={[styles.innerButton, { width: size, height: size, borderRadius: size / 2 }]}>
          <Text style={styles.sosText}>SOS</Text>
          <Text style={[
            styles.subText,
            isHolding && styles.subTextHolding,
            triggered && styles.subTextTriggered,
          ]}>
            {holdText}
          </Text>
        </View>
        {isHolding && !triggered && (
          <View style={[
            styles.progressRing,
            { width: middleRingSize, height: middleRingSize },
          ]}>
            <Animated.View
              style={[
                styles.progressArc,
                {
                  transform: [
                    { rotate: `${holdProgress * 360 - 90}deg` },
                  ],
                },
              ]}
            />
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  outerContainer: {
    borderRadius: 9999,
    backgroundColor: colors.sosRingOuter,
    alignItems: 'center',
    justifyContent: 'center',
  },
  middleRing: {
    borderRadius: 9999,
    backgroundColor: colors.sosRing,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  innerButton: {
    backgroundColor: colors.sosButton,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1,
  },
  sosText: {
    fontSize: typography.fontSize.xxxl,
    fontWeight: typography.fontWeight.extraBold,
    color: colors.white,
  },
  subText: {
    fontSize: typography.fontSize.xs,
    color: colors.white,
    marginTop: spacing.xxs,
    opacity: 0.9,
    textAlign: 'center',
  },
  subTextHolding: {
    color: colors.warning,
    fontWeight: typography.fontWeight.bold,
  },
  subTextTriggered: {
    color: colors.info,
    fontWeight: typography.fontWeight.bold,
  },
  progressRing: {
    position: 'absolute',
    top: 0,
    left: 0,
    borderRadius: 9999,
    overflow: 'hidden',
  },
  progressArc: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    borderRadius: 9999,
    borderWidth: 4,
    borderColor: colors.warning,
    borderRightColor: 'transparent',
    borderBottomColor: 'transparent',
    transform: [{ rotate: '-90deg' }],
  },
});