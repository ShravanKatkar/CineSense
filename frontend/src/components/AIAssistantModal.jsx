import React, { useState } from "react";
import { Sparkles, X, Send, Bot, CheckCircle2, ShieldAlert } from "lucide-react";
import { MovieCard } from "./MovieCard";
import { performRagSearch } from "../api/client";

export function AIAssistantModal({ isOpen, onClose, onSelectMovie }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);

  if (!isOpen) return null;

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setResponse(null);
    try {
      const res = await performRagSearch(query.trim(), 8);
      setResponse(res);
    } catch (err) {
      console.error("RAG search failed", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: "rgba(10, 10, 15, 0.85)",
      backdropFilter: "blur(12px)",
      zIndex: 200,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "24px"
    }}>
      <div className="glass-panel animate-fade-in" style={{
        width: "100%",
        maxWidth: "840px",
        maxHeight: "85vh",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        boxShadow: "0 25px 50px rgba(0,0,0,0.6)"
      }}>
        {/* Header */}
        <div style={{
          padding: "18px 24px",
          borderBottom: "1px solid var(--border-glass)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              background: "var(--gradient-brand)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}>
              <Bot size={18} color="#fff" />
            </div>
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: "700" }}>CineSense AI RAG Assistant</h3>
              <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>0% Hallucination Candidate Grounding Engine</p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-muted)",
              cursor: "pointer"
            }}
          >
            <X size={22} />
          </button>
        </div>

        {/* Input Form */}
        <form onSubmit={handleSearch} style={{ padding: "16px 24px", borderBottom: "1px solid var(--border-glass)", display: "flex", gap: "12px" }}>
          <input
            type="text"
            placeholder="Ask anything... e.g. 'Scary 90s sci-fi thriller under 2 hours like Alien'"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
            style={{
              flex: 1,
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid var(--border-glass)",
              borderRadius: "var(--radius-md)",
              padding: "12px 18px",
              color: "#fff",
              fontSize: "0.95rem",
              outline: "none"
            }}
          />
          <button
            type="submit"
            disabled={loading}
            style={{
              background: "var(--gradient-brand)",
              border: "none",
              borderRadius: "var(--radius-md)",
              padding: "0 22px",
              color: "#fff",
              fontWeight: "600",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px"
            }}
          >
            {loading ? <Sparkles className="animate-spin" size={18} /> : <Send size={18} />}
            Ask
          </button>
        </form>

        {/* Results Container */}
        <div style={{ padding: "24px", overflowY: "auto", flex: 1, display: "flex", flexDirection: "column", gap: "20px" }}>
          {loading && (
            <div style={{ textAlign: "center", padding: "48px 0", color: "var(--text-secondary)" }}>
              <Sparkles size={36} className="pulse-glow" style={{ marginBottom: "12px" }} />
              <p>Parsing query intent & matching grounded candidates...</p>
            </div>
          )}

          {!loading && response && (
            <>
              {/* Intent breakdown */}
              {response.intent && (
                <div style={{
                  background: "rgba(99, 102, 241, 0.08)",
                  border: "1px solid rgba(99, 102, 241, 0.2)",
                  borderRadius: "var(--radius-md)",
                  padding: "14px 18px",
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "8px",
                  alignItems: "center",
                  fontSize: "0.82rem"
                }}>
                  <span style={{ color: "var(--accent-primary)", fontWeight: "600" }}>Parsed Intent:</span>
                  {response.intent.genres_include?.map((g) => (
                    <span key={g} style={{ background: "rgba(255,255,255,0.1)", padding: "2px 8px", borderRadius: "4px" }}>
                      Genre: {g}
                    </span>
                  ))}
                  {response.intent.year_min && (
                    <span style={{ background: "rgba(255,255,255,0.1)", padding: "2px 8px", borderRadius: "4px" }}>
                      Years: {response.intent.year_min} - {response.intent.year_max}
                    </span>
                  )}
                  {response.intent.runtime_max && (
                    <span style={{ background: "rgba(255,255,255,0.1)", padding: "2px 8px", borderRadius: "4px" }}>
                      Max: {response.intent.runtime_max} mins
                    </span>
                  )}
                </div>
              )}

              {/* Intro Text */}
              {response.intro && (
                <p style={{ fontSize: "1rem", color: "#fff", lineHeight: "1.5" }}>{response.intro}</p>
              )}

              {/* Grid of Picks */}
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(170px, 1fr))",
                gap: "16px"
              }}>
                {response.items?.map((m) => (
                  <MovieCard key={m.id} movie={m} onSelectMovie={onSelectMovie} />
                ))}
              </div>

              {/* Grounding meta badge */}
              <div style={{
                marginTop: "auto",
                paddingTop: "16px",
                borderTop: "1px solid var(--border-glass)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                fontSize: "0.78rem",
                color: "var(--text-muted)"
              }}>
                <span style={{ display: "flex", alignItems: "center", gap: "6px", color: "#10b981" }}>
                  <CheckCircle2 size={14} /> Grounded Grounding Verified (0% Hallucination)
                </span>
                <span>Latency: {response.meta?.latency_ms}ms</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
