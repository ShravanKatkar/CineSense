import React, { useState, useRef, useEffect } from "react";
import {
  X,
  Send,
  Sparkles,
  Bot,
  User,
  Zap,
  Star,
  Heart,
  ChevronRight,
  Loader2,
} from "lucide-react";
import { C } from "../../constants/theme";
import { normalizeMovie } from "../../utils/normalizers";

const SUGGESTIONS = [
  "Mind-bending sci-fi under 2 hours",
  "Best Marathi thrillers with a plot twist",
  "Movies similar to Interstellar but more emotional",
  "Compare Inception vs Arrival",
];

export default function ChatModal({
  isOpen,
  onClose,
  onOpenDetails,
  likedIds,
  onToggleLike,
}) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Greetings! I'm CineSense, your AI cinema discovery companion. Ask me for recommendations, compare films, or describe any mood or theme you're craving.",
      tools: [],
      items: [],
    },
  ]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!isOpen) return null;

  const sendMessage = async (textToSend) => {
    const text = (textToSend || input).trim();
    if (!text || isStreaming) return;

    setInput("");
    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setIsStreaming(true);

    const assistantMsgIndex = messages.length + 1;
    const initialAssistantMsg = {
      role: "assistant",
      content: "",
      tools: [],
      items: [],
    };
    setMessages((prev) => [...prev, initialAssistantMsg]);

    try {
      const response = await fetch("/api/v1/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text, k: 6 }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep last incomplete line

        let currentEvent = null;

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith("data: ") && currentEvent) {
            try {
              const data = JSON.parse(line.slice(6).trim());

              if (currentEvent === "tool_call") {
                setMessages((prev) => {
                  const copy = [...prev];
                  const cur = copy[copy.length - 1];
                  if (cur) {
                    cur.tools = [
                      ...cur.tools,
                      { name: data.tool, args: data.args },
                    ];
                  }
                  return copy;
                });
              } else if (currentEvent === "token") {
                setMessages((prev) => {
                  const copy = [...prev];
                  const cur = copy[copy.length - 1];
                  if (cur) {
                    cur.content += data.token;
                  }
                  return copy;
                });
              } else if (currentEvent === "results") {
                setMessages((prev) => {
                  const copy = [...prev];
                  const cur = copy[copy.length - 1];
                  if (cur && data.items) {
                    cur.items = data.items.map(normalizeMovie).filter(Boolean);
                  }
                  return copy;
                });
              }
            } catch (e) {
              // ignore parse errors on partial frames
            }
          }
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const copy = [...prev];
        const cur = copy[copy.length - 1];
        if (cur) {
          cur.content =
            "I encountered a temporary connection issue. Please make sure the backend server is running.";
        }
        return copy;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 60,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1rem",
        background: "rgba(10, 8, 14, 0.78)",
        backdropFilter: "blur(12px)",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 720,
          height: "82vh",
          background: C.surface,
          border: `1px solid ${C.border}`,
          display: "flex",
          flexDirection: "column",
          position: "relative",
          boxShadow: "0 24px 60px rgba(0,0,0,0.6)",
          overflow: "hidden",
        }}
      >
        {/* Grain overlay */}
        <div className="grain-overlay" />

        {/* Modal Header */}
        <div
          style={{
            padding: "16px 20px",
            borderBottom: `1px solid ${C.border}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: C.surfaceHigh,
            zIndex: 2,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div
              style={{
                width: 32,
                height: 32,
                background: C.accentDim,
                borderRadius: 4,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Sparkles size={18} color={C.accent} />
            </div>
            <div>
              <h3
                className="font-display"
                style={{
                  fontSize: "1.25rem",
                  color: C.text,
                  lineHeight: 1,
                  letterSpacing: "-0.01em",
                }}
              >
                CineSense AI Assistant
              </h3>
              <span
                style={{
                  fontSize: "0.7rem",
                  color: C.teal,
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  marginTop: 2,
                }}
              >
                <span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: "#4ade80",
                    display: "inline-block",
                  }}
                />
                Llama 3.3 70B & Hybrid RecSys Active
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              color: C.muted,
              cursor: "pointer",
              padding: 6,
              borderRadius: "50%",
              display: "flex",
              transition: "color 0.2s",
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Messages List */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "20px",
            display: "flex",
            flexDirection: "column",
            gap: 18,
            zIndex: 2,
          }}
        >
          {messages.map((m, idx) => (
            <div
              key={idx}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: m.role === "user" ? "flex-end" : "flex-start",
              }}
            >
              {/* Message bubble */}
              <div
                style={{
                  maxWidth: "85%",
                  background: m.role === "user" ? C.surfaceHigh : "#201824",
                  border: `1px solid ${
                    m.role === "user" ? C.accentDim : C.border
                  }`,
                  padding: "12px 16px",
                  fontSize: "0.875rem",
                  lineHeight: 1.6,
                  color: C.text,
                  position: "relative",
                }}
              >
                {/* Formatted Message Content */}
                <div style={{ whiteSpace: "pre-wrap" }}>
                  {m.role === "assistant" && m.content
                    ? m.content.split("\n").map((line, lIdx) => {
                        const parts = line.split(/(\*\*.*?\*\*)/g);
                        return (
                          <div
                            key={lIdx}
                            style={{
                              minHeight: line.trim() ? "auto" : "0.5rem",
                              marginBottom: line.startsWith("•") || line.startsWith("-") ? 6 : 4,
                            }}
                          >
                            {parts.map((part, pIdx) => {
                              if (part.startsWith("**") && part.endsWith("**")) {
                                return (
                                  <strong
                                    key={pIdx}
                                    style={{
                                      color: C.accent,
                                      fontWeight: 700,
                                      letterSpacing: "0.01em",
                                    }}
                                  >
                                    {part.slice(2, -2)}
                                  </strong>
                                );
                              }
                              return part;
                            })}
                          </div>
                        );
                      })
                    : m.content}
                </div>

                {/* Verified Movie Recommendation Cards */}
                {m.items?.length > 0 && (
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns:
                        "repeat(auto-fill, minmax(180px, 1fr))",
                      gap: 12,
                      marginTop: 14,
                      paddingTop: 12,
                      borderTop: `1px solid ${C.border}`,
                    }}
                  >
                    {m.items.map((movie) => (
                      <div
                        key={movie.id}
                        onClick={() => onOpenDetails(movie)}
                        style={{
                          background: C.surface,
                          border: `1px solid ${C.border}`,
                          padding: 8,
                          cursor: "pointer",
                          transition: "border-color 0.2s",
                        }}
                        onMouseEnter={(e) =>
                          (e.currentTarget.style.borderColor = C.accent)
                        }
                        onMouseLeave={(e) =>
                          (e.currentTarget.style.borderColor = C.border)
                        }
                      >
                        <div
                          style={{
                            width: "100%",
                            paddingTop: "135%",
                            position: "relative",
                            overflow: "hidden",
                            background: C.surfaceHigh,
                          }}
                        >
                          {movie.poster_url ? (
                            <img
                              src={movie.poster_url}
                              alt={movie.title}
                              style={{
                                position: "absolute",
                                inset: 0,
                                width: "100%",
                                height: "100%",
                                objectFit: "cover",
                              }}
                            />
                          ) : (
                            <div
                              style={{
                                position: "absolute",
                                inset: 0,
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                color: C.muted,
                              }}
                            >
                              <span className="font-display">
                                {movie.title.charAt(0)}
                              </span>
                            </div>
                          )}
                        </div>
                        <div style={{ paddingTop: 6 }}>
                          <h4
                            className="font-display"
                            style={{
                              fontSize: "0.95rem",
                              color: C.text,
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {movie.title}
                          </h4>
                          <div
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              fontSize: "0.7rem",
                              color: C.muted,
                              marginTop: 2,
                            }}
                          >
                            <span>{movie.year}</span>
                            <span
                              style={{
                                color: C.accent,
                                fontWeight: 700,
                                display: "flex",
                                alignItems: "center",
                                gap: 2,
                              }}
                            >
                              <Star size={9} fill={C.accent} />
                              {movie.rating}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {isStreaming && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                color: C.accent,
                fontSize: "0.78rem",
              }}
            >
              <Loader2
                size={14}
                style={{ animation: "rotateSlow 1s linear infinite" }}
              />
              CineSense is reasoning over movie databases & tools...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggestion Chips */}
        <div
          style={{
            padding: "8px 20px",
            display: "flex",
            gap: 8,
            overflowX: "auto",
            borderTop: `1px solid ${C.border}`,
            background: C.surface,
            zIndex: 2,
          }}
          className="no-scrollbar"
        >
          {SUGGESTIONS.map((s, idx) => (
            <button
              key={idx}
              onClick={() => sendMessage(s)}
              disabled={isStreaming}
              style={{
                background: C.surfaceHigh,
                border: `1px solid ${C.border}`,
                color: C.muted,
                padding: "4px 10px",
                fontSize: "0.72rem",
                borderRadius: 2,
                cursor: "pointer",
                whiteSpace: "nowrap",
                transition: "color 0.2s, border-color 0.2s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = C.accent;
                e.currentTarget.style.borderColor = C.accent;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = C.muted;
                e.currentTarget.style.borderColor = C.border;
              }}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div
          style={{
            padding: "14px 20px",
            borderTop: `1px solid ${C.border}`,
            background: C.surfaceHigh,
            zIndex: 2,
          }}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage();
            }}
            style={{ display: "flex", gap: 10 }}
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything (e.g. 'Recommend high-concept sci-fi movies similar to Arrival')..."
              style={{
                flex: 1,
                background: C.surface,
                border: `1px solid ${C.border}`,
                color: C.text,
                padding: "10px 14px",
                fontSize: "0.85rem",
                fontFamily: "'Work Sans', sans-serif",
                outline: "none",
              }}
            />
            <button
              type="submit"
              disabled={isStreaming || !input.trim()}
              className="cta-btn"
              style={{
                background: C.accent,
                color: C.bg,
                border: "none",
                padding: "0 18px",
                fontWeight: 700,
                fontSize: "0.85rem",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
                opacity: isStreaming || !input.trim() ? 0.5 : 1,
              }}
            >
              <Send size={15} />
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
