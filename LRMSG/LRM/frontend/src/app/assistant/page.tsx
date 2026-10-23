"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  Send,
  Sparkles,
  RotateCcw,
  BookOpen,
  AlertTriangle,
  Info,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  ArrowLeft,
  Mountain,
} from "lucide-react";
import {
  AssistantChatMessage,
  initWebAssistantSession,
  sendAssistantQuery,
  SUGGESTED_QUESTIONS,
} from "@/lib/assistant";

let messageCounter = 0;
function generateMessageId(prefix: string): string {
  messageCounter += 1;
  return `${prefix}-${Date.now()}-${messageCounter}`;
}

function getFormattedTime(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function AssistantPage() {
  const [messages, setMessages] = useState<AssistantChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [initError, setInitError] = useState<string | null>(null);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Initialize web assistant session once on mount (sets HttpOnly cookie)
  useEffect(() => {
    let isMounted = true;
    async function initSession() {
      try {
        await initWebAssistantSession();
        if (isMounted) {
          setInitError(null);
        }
      } catch (err) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Failed to initialize session";
          setInitError(msg);
        }
      }
    }
    initSession();
    return () => {
      isMounted = false;
    };
  }, []);

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const toggleSourceExpansion = (messageId: string) => {
    setExpandedSources((prev) => ({
      ...prev,
      [messageId]: !prev[messageId],
    }));
  };

  const handleSend = async (queryText?: string) => {
    const textToSend = (queryText ?? inputQuery).trim();
    if (!textToSend || isLoading) return;

    if (textToSend.length < 2) return;
    if (textToSend.length > 1000) return;

    const userMessage: AssistantChatMessage = {
      id: generateMessageId("user"),
      sender: "user",
      text: textToSend,
      timestamp: getFormattedTime(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery("");
    setIsLoading(true);

    try {
      const response = await sendAssistantQuery(textToSend);

      const assistantMessage: AssistantChatMessage = {
        id: generateMessageId("asst"),
        sender: "assistant",
        text: response.reply,
        sources: response.sources,
        disclaimer: response.disclaimer,
        fallbackMode: response.fallback_mode,
        timestamp: getFormattedTime(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "An unexpected error occurred while communicating with the assistant.";

      const errorMessage: AssistantChatMessage = {
        id: generateMessageId("err"),
        sender: "assistant",
        text: errorMsg,
        timestamp: getFormattedTime(),
        isError: true,
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      // Refocus textarea on desktop
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleResetSession = async () => {
    setMessages([]);
    setIsLoading(true);
    try {
      await initWebAssistantSession();
      setInitError(null);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to reset session";
      setInitError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetryLast = () => {
    // Find the last user message
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].sender === "user") {
        const lastQuery = messages[i].text;
        // Remove subsequent error messages
        setMessages((prev) => prev.slice(0, i));
        handleSend(lastQuery);
        break;
      }
    }
  };

  return (
    <main
      style={{
        backgroundColor: "#F5EEE6",
        minHeight: "calc(100vh - 64px)",
        color: "#231F20",
        fontFamily: "'DM Sans', sans-serif",
      }}
      className="flex flex-col"
    >
      {/* ── TOP HEADER / BREADCRUMB ── */}
      <section
        style={{
          borderBottom: "1px solid #D6CCC8",
          backgroundColor: "#FAF4EC",
        }}
        className="px-4 py-3 sm:px-6 sm:py-4"
      >
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex items-center justify-center w-8 h-8 rounded-lg border border-[#D6CCC8] bg-[#F5EEE6] text-[#736B63] hover:text-[#231F20] transition-colors"
              title="Return to Home"
              aria-label="Return to Home"
            >
              <ArrowLeft size={16} />
            </Link>
            <div className="flex items-center gap-2">
              <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-[#8E3A1A] text-white shadow-sm">
                <Sparkles size={18} />
              </div>
              <div>
                <h1
                  style={{
                    fontFamily: "'Space Grotesk', sans-serif",
                    letterSpacing: "-0.5px",
                  }}
                  className="text-lg sm:text-xl font-bold text-[#231F20] leading-tight"
                >
                  BhuRakshak AI Assistant
                </h1>
                <p className="text-xs text-[#736B63] font-medium">
                  Landslide Knowledge, Risk Factors &amp; Science Companion
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-auto">
            <button
              type="button"
              onClick={handleResetSession}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-md border border-[#D6CCC8] bg-[#FAF4EC] text-[#736B63] hover:bg-[#F5EEE6] hover:text-[#231F20] disabled:opacity-50 transition-colors cursor-pointer"
              title="Reset conversation and start fresh session"
              aria-label="New Conversation"
            >
              <RotateCcw size={13} />
              <span>New Chat</span>
            </button>
          </div>
        </div>
      </section>

      {/* ── SAFETY & EDUCATIONAL DISCLAIMER BANNER ── */}
      <div
        style={{
          backgroundColor: "rgba(142, 58, 26, 0.06)",
          borderBottom: "1px solid rgba(142, 58, 26, 0.15)",
        }}
        className="px-4 py-2 sm:px-6"
      >
        <div className="max-w-4xl mx-auto flex items-start gap-2 text-xs text-[#8E3A1A] font-medium leading-relaxed">
          <Info size={15} className="mt-0.5 shrink-0" />
          <span>
            <strong>Informational Companion:</strong> BhuRakshak AI provides educational guidance on landslide
            processes, terrain factors, and early-warning concepts. It is <em>not</em> an emergency dispatch system or
            certified prediction engine. In immediate danger, contact local emergency services or NDMA.
          </span>
        </div>
      </div>

      {initError && (
        <div
          style={{
            backgroundColor: "#FEF2F2",
            borderBottom: "1px solid #FECACA",
          }}
          className="px-4 py-2 sm:px-6"
        >
          <div className="max-w-4xl mx-auto flex items-center justify-between text-xs text-[#DC2626]">
            <div className="flex items-center gap-2">
              <AlertTriangle size={14} className="shrink-0" />
              <span>Session notice: {initError}. Live queries will automatically attempt to reconnect.</span>
            </div>
            <button
              onClick={handleResetSession}
              className="underline font-semibold cursor-pointer hover:text-red-800"
            >
              Reconnect
            </button>
          </div>
        </div>
      )}

      {/* ── CONVERSATION CONTAINER ── */}
      <div className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 flex flex-col">
        {messages.length === 0 ? (
          /* ── EMPTY STATE & SUGGESTED PROMPTS ── */
          <div className="my-auto py-6 sm:py-10 flex flex-col items-center text-center">
            <div className="w-14 h-14 rounded-2xl bg-[#FAF4EC] border border-[#D6CCC8] flex items-center justify-center text-[#8E3A1A] shadow-sm mb-4">
              <Mountain size={28} />
            </div>
            <h2
              style={{ fontFamily: "'Space Grotesk', sans-serif" }}
              className="text-xl sm:text-2xl font-bold text-[#231F20] mb-2"
            >
              Ask BhuRakshak About Landslide Science
            </h2>
            <p className="text-sm text-[#736B63] max-w-lg mb-8 leading-relaxed">
              Explore how rainfall, soil moisture, geological terrain features, satellite radar, and machine learning
              models work together in landslide risk prediction and early warning.
            </p>

            <div className="w-full max-w-2xl text-left">
              <span
                style={{ fontFamily: "'DM Mono', monospace" }}
                className="text-[11px] font-bold text-[#8E3A1A] tracking-wider uppercase block mb-3"
              >
                Suggested Explorations
              </span>
              <div className="grid grid-cols-1 gap-2.5">
                {SUGGESTED_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSend(q)}
                    disabled={isLoading}
                    className="flex items-start gap-3 p-3.5 rounded-xl border border-[#D6CCC8] bg-[#FAF4EC] text-[#231F20] hover:bg-white hover:border-[#8E3A1A] hover:shadow-sm text-sm text-left transition-all cursor-pointer group disabled:opacity-50"
                  >
                    <span className="flex items-center justify-center w-5 h-5 rounded-full bg-[#E6D6C3] text-[#8E3A1A] text-xs font-bold shrink-0 mt-0.5 group-hover:bg-[#8E3A1A] group-hover:text-white transition-colors">
                      {idx + 1}
                    </span>
                    <span className="flex-1 font-medium">{q}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* ── ACTIVE CHAT MESSAGES ── */
          <div className="flex flex-col gap-4 mb-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
              >
                {/* Sender label and timestamp */}
                <div className="flex items-center gap-1.5 px-1 mb-1 text-[11px] text-[#736B63] font-medium">
                  {msg.sender === "user" ? (
                    <span>You • {msg.timestamp}</span>
                  ) : (
                    <span className="flex items-center gap-1 font-semibold text-[#8E3A1A]">
                      <Sparkles size={11} />
                      BhuRakshak Assistant • {msg.timestamp}
                    </span>
                  )}
                </div>

                {/* Message Bubble */}
                <div
                  style={{
                    backgroundColor: msg.sender === "user" ? "#8E3A1A" : msg.isError ? "#FEF2F2" : "#FAF4EC",
                    color: msg.sender === "user" ? "#FFFFFF" : msg.isError ? "#991B1B" : "#231F20",
                    borderColor: msg.isError ? "#FECACA" : "#D6CCC8",
                  }}
                  className={`max-w-[90%] sm:max-w-[80%] rounded-2xl p-4 sm:p-5 border shadow-sm ${
                    msg.sender === "user" ? "rounded-br-sm text-white" : "rounded-bl-sm"
                  }`}
                >
                  {/* Fallback Mode Badge */}
                  {msg.fallbackMode && (
                    <div className="flex items-center gap-1.5 mb-3 px-2.5 py-1 rounded-md bg-[#FEF3C7] border border-[#FDE68A] text-[#92400E] text-xs font-semibold">
                      <AlertTriangle size={13} className="shrink-0" />
                      <span>Offline Safety Mode Active — Knowledge base degraded</span>
                    </div>
                  )}

                  {/* Main text content (safe plain text rendering with preserved paragraphs) */}
                  <div className="whitespace-pre-wrap text-sm leading-relaxed space-y-2">
                    {msg.text}
                  </div>

                  {/* Retry action for error messages */}
                  {msg.isError && (
                    <div className="mt-3 pt-2 border-t border-[#FECACA] flex items-center justify-between">
                      <span className="text-xs text-[#B91C1C]">Communication failed</span>
                      <button
                        type="button"
                        onClick={handleRetryLast}
                        className="flex items-center gap-1 text-xs font-bold text-[#8E3A1A] hover:underline cursor-pointer"
                      >
                        <RotateCcw size={12} />
                        Retry Query
                      </button>
                    </div>
                  )}

                  {/* Curated Sources & Citations */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-[#E6D6C3]">
                      <button
                        type="button"
                        onClick={() => toggleSourceExpansion(msg.id)}
                        className="w-full flex items-center justify-between text-xs font-bold text-[#8E3A1A] hover:text-[#231F20] transition-colors cursor-pointer"
                        aria-expanded={expandedSources[msg.id] ?? true}
                      >
                        <span className="flex items-center gap-1.5">
                          <BookOpen size={13} />
                          Retrieved Sources ({msg.sources.length})
                        </span>
                        {expandedSources[msg.id] === false ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
                      </button>

                      {(expandedSources[msg.id] ?? true) && (
                        <div className="mt-2.5 space-y-1.5">
                          {msg.sources.map((src, sIdx) => (
                            <div
                              key={sIdx}
                              className="p-2.5 rounded-lg border border-[#E6D6C3] bg-[#F5EEE6] text-xs flex flex-col gap-0.5"
                            >
                              <div className="flex items-center justify-between gap-2">
                                <span className="font-semibold text-[#231F20] truncate">
                                  {src.title}
                                </span>
                                {src.is_curated && (
                                  <span className="flex items-center gap-0.5 text-[10px] font-bold text-[#2E7D32] bg-[#E8F5E9] px-1.5 py-0.5 rounded shrink-0">
                                    <ShieldCheck size={10} />
                                    Curated
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-2 text-[10px] text-[#736B63]">
                                <span
                                  style={{ fontFamily: "'DM Mono', monospace" }}
                                  className="font-medium"
                                >
                                  ID: {src.document_id}
                                </span>
                                {src.category && (
                                  <>
                                    <span>•</span>
                                    <span>Category: {src.category}</span>
                                  </>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Safety Disclaimer */}
                  {msg.disclaimer && (
                    <div className="mt-3 pt-2 border-t border-[#E6D6C3]/60 text-[11px] text-[#736B63] italic">
                      {msg.disclaimer}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* In-flight loading indicator */}
            {isLoading && (
              <div className="flex flex-col items-start">
                <div className="flex items-center gap-1.5 px-1 mb-1 text-[11px] text-[#8E3A1A] font-semibold">
                  <Sparkles size={11} />
                  BhuRakshak Assistant
                </div>
                <div
                  style={{
                    backgroundColor: "#FAF4EC",
                    borderColor: "#D6CCC8",
                  }}
                  className="rounded-2xl rounded-bl-sm p-4 border shadow-sm flex items-center gap-3 text-xs text-[#736B63]"
                >
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-[#8E3A1A] animate-bounce [animation-delay:-0.3s]" />
                    <span className="w-2 h-2 rounded-full bg-[#8E3A1A] animate-bounce [animation-delay:-0.15s]" />
                    <span className="w-2 h-2 rounded-full bg-[#8E3A1A] animate-bounce" />
                  </div>
                  <span className="font-medium">Consulting landslide knowledge base...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* ── INPUT CONTROL BAR ── */}
      <section
        style={{
          borderTop: "1px solid #D6CCC8",
          backgroundColor: "#FAF4EC",
        }}
        className="sticky bottom-0 z-20 px-4 py-3 sm:px-6"
      >
        <div className="max-w-4xl mx-auto flex flex-col gap-2">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-end gap-2.5"
          >
            <div className="relative flex-1">
              <textarea
                ref={textareaRef}
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading}
                placeholder="Ask about landslide mechanisms, rainfall triggers, GIS layers, or early warning..."
                maxLength={1000}
                rows={1}
                aria-label="Ask a question about landslide science"
                style={{
                  backgroundColor: "#F5EEE6",
                  borderColor: "#D6CCC8",
                  minHeight: "44px",
                  maxHeight: "130px",
                }}
                className="w-full resize-none rounded-xl border px-3.5 py-2.5 text-sm text-[#231F20] placeholder-[#8A8178] focus:border-[#8E3A1A] focus:outline-none focus:ring-1 focus:ring-[#8E3A1A] disabled:opacity-60 transition-colors"
              />
              <div className="absolute right-3 bottom-2 text-[10px] text-[#8A8178] font-mono pointer-events-none">
                {inputQuery.length}/1000
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || inputQuery.trim().length < 2}
              aria-label="Send question"
              style={{
                backgroundColor: inputQuery.trim().length >= 2 && !isLoading ? "#8E3A1A" : "#D6CCC8",
                color: "#FFFFFF",
                height: "44px",
                width: "44px",
              }}
              className="flex items-center justify-center rounded-xl shadow-sm transition-all cursor-pointer disabled:cursor-not-allowed shrink-0"
            >
              <Send size={18} />
            </button>
          </form>

          <div className="flex items-center justify-between text-[11px] text-[#736B63] px-1">
            <span>
              Press <kbd className="px-1 py-0.5 rounded bg-[#E6D6C3] text-[#231F20] font-mono text-[10px]">Enter</kbd> to send,{" "}
              <kbd className="px-1 py-0.5 rounded bg-[#E6D6C3] text-[#231F20] font-mono text-[10px]">Shift+Enter</kbd> for newline
            </span>
            <span>Grounding: 6 Curated Landslide Articles</span>
          </div>
        </div>
      </section>
    </main>
  );
}
