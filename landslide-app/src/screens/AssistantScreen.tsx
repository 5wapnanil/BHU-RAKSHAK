import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { typography, spacing, borderRadius } from '../theme';
import { useLanguage } from '../i18n';
import {
  mobileAssistantService,
  MobileAssistantMessage,
  MOBILE_SUGGESTED_QUESTIONS,
} from '../services/api/assistantApi';

let messageCounter = 0;
function generateMessageId(prefix: string): string {
  messageCounter += 1;
  return `${prefix}-${Date.now()}-${messageCounter}`;
}

function getFormattedTime(): string {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

interface AssistantScreenProps {
  navigation: any;
}

export function AssistantScreen({ navigation }: AssistantScreenProps) {
  const { t } = useLanguage();
  const [messages, setMessages] = useState<MobileAssistantMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [initError, setInitError] = useState<string | null>(null);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});

  const scrollViewRef = useRef<ScrollView>(null);
  const isSendingRef = useRef(false);

  // Initialize session in background on mount
  useEffect(() => {
    let isMounted = true;
    mobileAssistantService
      .initSession()
      .then(() => {
        if (isMounted) setInitError(null);
      })
      .catch((err) => {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : 'Session initialization error';
          setInitError(msg);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const scrollToBottom = () => {
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  const toggleSources = (msgId: string) => {
    setExpandedSources((prev) => ({
      ...prev,
      [msgId]: !(prev[msgId] ?? true),
    }));
  };

  const handleSend = async (queryOverride?: string) => {
    const textToSend = (queryOverride ?? inputText).trim();
    if (!textToSend || isLoading || isSendingRef.current) return;

    if (textToSend.length < 2 || textToSend.length > 1000) return;

    isSendingRef.current = true;
    const userMsg: MobileAssistantMessage = {
      id: generateMessageId('user'),
      sender: 'user',
      text: textToSend,
      timestamp: getFormattedTime(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);
    scrollToBottom();

    try {
      const response = await mobileAssistantService.query(textToSend);

      const assistantMsg: MobileAssistantMessage = {
        id: generateMessageId('asst'),
        sender: 'assistant',
        text: response.reply,
        sources: response.sources,
        disclaimer: response.disclaimer,
        fallbackMode: response.fallback_mode,
        timestamp: getFormattedTime(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setInitError(null);
    } catch (err) {
      const errMsg =
        err instanceof Error ? err.message : 'Failed to reach assistant. Please check your network connection.';

      const errorMsg: MobileAssistantMessage = {
        id: generateMessageId('err'),
        sender: 'assistant',
        text: errMsg,
        timestamp: getFormattedTime(),
        isError: true,
      };

      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      isSendingRef.current = false;
      setIsLoading(false);
      scrollToBottom();
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    mobileAssistantService.resetSession();
    setIsLoading(true);
    mobileAssistantService
      .initSession()
      .then(() => setInitError(null))
      .catch((err) => setInitError(err.message))
      .finally(() => setIsLoading(false));
  };

  const handleRetryLast = () => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].sender === 'user') {
        const lastQuery = messages[i].text;
        setMessages((prev) => prev.slice(0, i));
        handleSend(lastQuery);
        break;
      }
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      {/* ── SCREEN HEADER ── */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
          accessibilityLabel="Go back"
          accessibilityRole="button"
        >
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>

        <View style={styles.headerCenter}>
          <View style={styles.headerIconWrap}>
            <Ionicons name="sparkles" size={16} color={colors.white} />
          </View>
          <View>
            <Text style={styles.headerTitle}>BhuRakshak AI</Text>
            <Text style={styles.headerSubtitle}>Landslide Knowledge Companion</Text>
          </View>
        </View>

        <TouchableOpacity
          style={styles.newChatButton}
          onPress={handleNewChat}
          disabled={isLoading}
          accessibilityLabel="Start new chat"
          accessibilityRole="button"
        >
          <Ionicons name="refresh-outline" size={20} color={colors.textSecondary} />
        </TouchableOpacity>
      </View>

      {/* ── EDUCATIONAL / SAFETY BANNER ── */}
      <View style={styles.disclaimerBanner}>
        <Ionicons name="information-circle-outline" size={16} color={colors.primary} style={styles.disclaimerIcon} />
        <Text style={styles.disclaimerBannerText}>
          Educational tool on landslide science and risk factors. Not an emergency dispatch system. For active hazards, call 112.
        </Text>
      </View>

      {initError && (
        <View style={styles.errorNotice}>
          <Ionicons name="warning-outline" size={14} color={colors.error} />
          <Text style={styles.errorNoticeText}>Session notice: Reconnecting on next query.</Text>
        </View>
      )}

      {/* ── CONVERSATION / EMPTY AREA ── */}
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <ScrollView
          ref={scrollViewRef}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          onContentSizeChange={scrollToBottom}
        >
          {messages.length === 0 ? (
            /* ── EMPTY STATE & SUGGESTED TOPICS ── */
            <View style={styles.emptyContainer}>
              <View style={styles.emptyIconWrap}>
                <Ionicons name="earth" size={36} color={colors.primary} />
              </View>
              <Text style={styles.emptyTitle}>Ask BhuRakshak AI</Text>
              <Text style={styles.emptySubtitle}>
                Learn about physical warning signals, pore-water pressure, rainfall triggers, satellite radar, and early-warning systems.
              </Text>

              <View style={styles.suggestionsList}>
                <Text style={styles.suggestionsHeader}>SUGGESTED TOPICS</Text>
                {MOBILE_SUGGESTED_QUESTIONS.map((q, idx) => (
                  <TouchableOpacity
                    key={idx}
                    style={styles.suggestionCard}
                    onPress={() => handleSend(q)}
                    disabled={isLoading}
                    activeOpacity={0.7}
                  >
                    <View style={styles.suggestionNumberWrap}>
                      <Text style={styles.suggestionNumber}>{idx + 1}</Text>
                    </View>
                    <Text style={styles.suggestionText}>{q}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          ) : (
            /* ── MESSAGE STREAM ── */
            <View style={styles.messagesList}>
              {messages.map((msg) => (
                <View
                  key={msg.id}
                  style={[
                    styles.messageRow,
                    msg.sender === 'user' ? styles.userRow : styles.assistantRow,
                  ]}
                >
                  <Text style={styles.messageMeta}>
                    {msg.sender === 'user' ? `You • ${msg.timestamp}` : `BhuRakshak AI • ${msg.timestamp}`}
                  </Text>

                  <View
                    style={[
                      styles.bubble,
                      msg.sender === 'user'
                        ? styles.userBubble
                        : msg.isError
                        ? styles.errorBubble
                        : styles.assistantBubble,
                    ]}
                  >
                    {msg.fallbackMode && (
                      <View style={styles.fallbackBadge}>
                        <Ionicons name="cloud-offline-outline" size={12} color="#B45309" />
                        <Text style={styles.fallbackBadgeText}>Offline Safety Mode Active</Text>
                      </View>
                    )}

                    <Text
                      style={[
                        styles.bubbleText,
                        msg.sender === 'user'
                          ? styles.userBubbleText
                          : msg.isError
                          ? styles.errorBubbleText
                          : styles.assistantBubbleText,
                      ]}
                    >
                      {msg.text}
                    </Text>

                    {msg.isError && (
                      <TouchableOpacity
                        style={styles.retryButton}
                        onPress={handleRetryLast}
                        activeOpacity={0.7}
                      >
                        <Ionicons name="refresh" size={14} color={colors.primary} />
                        <Text style={styles.retryButtonText}>Retry Query</Text>
                      </TouchableOpacity>
                    )}

                    {/* Citations section */}
                    {msg.sources && msg.sources.length > 0 && (
                      <View style={styles.sourcesContainer}>
                        <TouchableOpacity
                          style={styles.sourcesToggle}
                          onPress={() => toggleSources(msg.id)}
                          activeOpacity={0.7}
                        >
                          <Ionicons name="book-outline" size={13} color={colors.primary} />
                          <Text style={styles.sourcesToggleText}>
                            Sources ({msg.sources.length})
                          </Text>
                          <Ionicons
                            name={expandedSources[msg.id] === false ? 'chevron-down' : 'chevron-up'}
                            size={14}
                            color={colors.textSecondary}
                          />
                        </TouchableOpacity>

                        {(expandedSources[msg.id] ?? true) && (
                          <View style={styles.sourcesContent}>
                            {msg.sources.map((src, sIdx) => (
                              <View key={sIdx} style={styles.sourceCard}>
                                <View style={styles.sourceCardTop}>
                                  <Text style={styles.sourceTitle} numberOfLines={1}>
                                    {src.title}
                                  </Text>
                                  {src.is_curated && (
                                    <View style={styles.curatedBadge}>
                                      <Text style={styles.curatedBadgeText}>Curated</Text>
                                    </View>
                                  )}
                                </View>
                                <Text style={styles.sourceId}>ID: {src.document_id}</Text>
                              </View>
                            ))}
                          </View>
                        )}
                      </View>
                    )}

                    {/* Safety Disclaimer */}
                    {msg.disclaimer && (
                      <Text style={styles.disclaimerText}>{msg.disclaimer}</Text>
                    )}
                  </View>
                </View>
              ))}

              {isLoading && (
                <View style={[styles.messageRow, styles.assistantRow]}>
                  <Text style={styles.messageMeta}>BhuRakshak AI • typing...</Text>
                  <View style={[styles.bubble, styles.assistantBubble, styles.loadingBubble]}>
                    <ActivityIndicator size="small" color={colors.primary} />
                    <Text style={styles.loadingText}>Consulting landslide knowledge base...</Text>
                  </View>
                </View>
              )}
            </View>
          )}
        </ScrollView>

        {/* ── INPUT BAR ── */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.inputField}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Ask about slope stability, rainfall, or GIS..."
            placeholderTextColor={colors.textLight}
            multiline
            maxLength={1000}
            editable={!isLoading}
          />
          <TouchableOpacity
            style={[
              styles.sendButton,
              inputText.trim().length >= 2 && !isLoading
                ? styles.sendButtonActive
                : styles.sendButtonDisabled,
            ]}
            onPress={() => handleSend()}
            disabled={isLoading || inputText.trim().length < 2}
            accessibilityLabel="Send message"
            accessibilityRole="button"
          >
            <Ionicons
              name="send"
              size={18}
              color={inputText.trim().length >= 2 && !isLoading ? colors.white : colors.textLight}
            />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    height: 56,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
    backgroundColor: colors.surface,
  },
  backButton: {
    padding: spacing.xs,
  },
  headerCenter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  headerIconWrap: {
    width: 28,
    height: 28,
    borderRadius: borderRadius.md,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
  },
  headerSubtitle: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondary,
  },
  newChatButton: {
    padding: spacing.xs,
  },
  disclaimerBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF0ED',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
    borderBottomWidth: 1,
    borderBottomColor: '#FADBD8',
  },
  disclaimerIcon: {
    marginRight: spacing.xs,
  },
  disclaimerBannerText: {
    fontSize: typography.fontSize.xs,
    color: colors.primaryDark,
    flex: 1,
    lineHeight: 14,
  },
  errorNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFEBEE',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    gap: spacing.xs,
  },
  errorNoticeText: {
    fontSize: typography.fontSize.xs,
    color: colors.error,
  },
  container: {
    flex: 1,
    backgroundColor: colors.backgroundLight,
  },
  scrollContent: {
    padding: spacing.md,
    flexGrow: 1,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: spacing.lg,
  },
  emptyIconWrap: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#FFF0ED',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  emptyTitle: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  emptySubtitle: {
    fontSize: typography.fontSize.md,
    color: colors.textSecondary,
    textAlign: 'center',
    paddingHorizontal: spacing.md,
    marginBottom: spacing.lg,
    lineHeight: 18,
  },
  suggestionsList: {
    width: '100%',
    gap: spacing.sm,
  },
  suggestionsHeader: {
    fontSize: typography.fontSize.xs,
    color: colors.primary,
    fontWeight: typography.fontWeight.bold,
    letterSpacing: 1,
    marginBottom: 4,
  },
  suggestionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.borderLight,
    gap: spacing.sm,
  },
  suggestionNumberWrap: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: '#FFF0ED',
    alignItems: 'center',
    justifyContent: 'center',
  },
  suggestionNumber: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.primary,
  },
  suggestionText: {
    fontSize: typography.fontSize.md,
    color: colors.text,
    flex: 1,
    lineHeight: 18,
  },
  messagesList: {
    gap: spacing.md,
  },
  messageRow: {
    maxWidth: '85%',
  },
  userRow: {
    alignSelf: 'flex-end',
    alignItems: 'flex-end',
  },
  assistantRow: {
    alignSelf: 'flex-start',
    alignItems: 'flex-start',
  },
  messageMeta: {
    fontSize: typography.fontSize.xs,
    color: colors.textLight,
    marginBottom: 2,
    marginHorizontal: 4,
  },
  bubble: {
    padding: spacing.md,
    borderRadius: borderRadius.lg,
  },
  userBubble: {
    backgroundColor: colors.primary,
    borderBottomRightRadius: 2,
  },
  assistantBubble: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.borderLight,
    borderBottomLeftRadius: 2,
  },
  errorBubble: {
    backgroundColor: '#FFEBEE',
    borderWidth: 1,
    borderColor: '#FFCDD2',
    borderBottomLeftRadius: 2,
  },
  loadingBubble: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.md,
  },
  loadingText: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
  },
  bubbleText: {
    fontSize: typography.fontSize.md,
    lineHeight: 20,
  },
  userBubbleText: {
    color: colors.white,
  },
  assistantBubbleText: {
    color: colors.text,
  },
  errorBubbleText: {
    color: colors.error,
  },
  fallbackBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    marginBottom: spacing.xs,
    alignSelf: 'flex-start',
  },
  fallbackBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#92400E',
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: spacing.sm,
    paddingTop: spacing.xs,
    borderTopWidth: 1,
    borderTopColor: '#FFCDD2',
  },
  retryButtonText: {
    fontSize: typography.fontSize.sm,
    color: colors.primary,
    fontWeight: typography.fontWeight.bold,
  },
  sourcesContainer: {
    marginTop: spacing.sm,
    paddingTop: spacing.xs,
    borderTopWidth: 1,
    borderTopColor: colors.borderLight,
  },
  sourcesToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 2,
  },
  sourcesToggleText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.bold,
    color: colors.primary,
    flex: 1,
  },
  sourcesContent: {
    marginTop: spacing.xs,
    gap: 4,
  },
  sourceCard: {
    backgroundColor: colors.surfaceGray,
    padding: spacing.xs + 2,
    borderRadius: borderRadius.sm,
  },
  sourceCardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 6,
  },
  sourceTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.text,
    flex: 1,
  },
  curatedBadge: {
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: 3,
  },
  curatedBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#2E7D32',
  },
  sourceId: {
    fontSize: 9,
    color: colors.textLight,
    marginTop: 2,
  },
  disclaimerText: {
    fontSize: typography.fontSize.xs,
    fontStyle: 'italic',
    color: colors.textLight,
    marginTop: spacing.xs + 2,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.borderLight,
    gap: spacing.sm,
  },
  inputField: {
    flex: 1,
    backgroundColor: colors.surfaceGray,
    borderRadius: borderRadius.lg,
    paddingHorizontal: spacing.md,
    paddingTop: Platform.OS === 'ios' ? 10 : 8,
    paddingBottom: Platform.OS === 'ios' ? 10 : 8,
    minHeight: 40,
    maxHeight: 100,
    fontSize: 14,
    color: colors.text,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: borderRadius.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonActive: {
    backgroundColor: colors.primary,
  },
  sendButtonDisabled: {
    backgroundColor: colors.borderLight,
  },
});
