import React, { useState } from "react";
import {
  X,
  Users,
  Plus,
  Trash2,
  Sparkles,
  ShieldAlert,
  ThumbsUp,
  Star,
  Film,
  ArrowRight,
  Loader2,
  Check,
} from "lucide-react";
import { C } from "../../constants/theme";
import { getMovieNightRecs } from "../../api/client";
import { normalizeMovie } from "../../utils/normalizers";

const POPULAR_GENRES = [
  "Action",
  "Adventure",
  "Animation",
  "Comedy",
  "Crime",
  "Drama",
  "Fantasy",
  "Horror",
  "Mystery",
  "Romance",
  "Sci-Fi",
  "Thriller",
];

export default function MovieNightModal({
  isOpen,
  onClose,
  onSelectMovieForDrawer,
}) {
  const [participants, setParticipants] = useState([
    { id: 1, name: "Arjun", genres: ["Sci-Fi", "Action"] },
    { id: 2, name: "Pooja", genres: ["Comedy", "Romance"] },
  ]);

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleAddParticipant = () => {
    if (participants.length >= 4) return;
    const newId = Date.now();
    setParticipants((prev) => [
      ...prev,
      { id: newId, name: `Viewer ${prev.length + 1}`, genres: ["Drama", "Thriller"] },
    ]);
  };

  const handleRemoveParticipant = (id) => {
    if (participants.length <= 2) return;
    setParticipants((prev) => prev.filter((p) => p.id !== id));
  };

  const handleUpdateName = (id, newName) => {
    setParticipants((prev) =>
      prev.map((p) => (p.id === id ? { ...p, name: newName } : p))
    );
  };

  const handleToggleGenre = (id, genre) => {
    setParticipants((prev) =>
      prev.map((p) => {
        if (p.id !== id) return p;
        const exists = p.genres.includes(genre);
        const updated = exists
          ? p.genres.filter((g) => g !== genre)
          : [...p.genres, genre];
        return { ...p, genres: updated };
      })
    );
  };

  const handleFindConsensus = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = participants.map((p) => ({
        name: p.name || "Viewer",
        favorite_genres: p.genres,
        seed_movie_titles: [],
      }));
      const res = await getMovieNightRecs(payload);
      setResults(res);
    } catch {
      setError("Unable to compute group consensus. Please check your selections.");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 90,
        background: "rgba(10,8,14,0.86)",
        backdropFilter: "blur(14px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "16px",
      }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        style={{
          background: C.surface,
          border: `1px solid ${C.borderBright}`,
          borderRadius: 8,
          width: "100%",
          maxWidth: "52rem",
          maxHeight: "92vh",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          boxShadow: "0 24px 60px rgba(0,0,0,0.85)",
          position: "relative",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "18px 24px",
            borderBottom: `1px solid ${C.border}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: C.surfaceHigh,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 6,
                background: C.accentDim,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Users size={18} color={C.accent} />
            </div>
            <div>
              <h2
                className="font-display"
                style={{
                  fontSize: "1.35rem",
                  color: C.text,
                  letterSpacing: "-0.01em",
                  lineHeight: 1.1,
                }}
              >
                AI GROUP MOVIE NIGHT
              </h2>
              <p style={{ fontSize: "0.78rem", color: C.muted }}>
                Multi-taste consensus engine with Least-Misery aggregation
              </p>
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
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: "20px 24px", overflowY: "auto", flex: 1 }}>
          {/* Participants Configuration */}
          <div style={{ marginBottom: 22 }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 12,
              }}
            >
              <h3 style={{ fontSize: "0.88rem", fontWeight: 700, color: C.text, textTransform: "uppercase" }}>
                Group Members ({participants.length}/4)
              </h3>
              {participants.length < 4 && (
                <button
                  onClick={handleAddParticipant}
                  style={{
                    background: C.surfaceHigh,
                    border: `1px solid ${C.border}`,
                    color: C.accent,
                    borderRadius: 4,
                    padding: "4px 10px",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: 5,
                  }}
                >
                  <Plus size={14} /> Add Person
                </button>
              )}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 12 }}>
              {participants.map((p, idx) => (
                <div
                  key={p.id}
                  style={{
                    background: C.surfaceHigh,
                    border: `1px solid ${C.border}`,
                    borderRadius: 6,
                    padding: "12px 16px",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: 8,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span
                        style={{
                          width: 22,
                          height: 22,
                          borderRadius: 99,
                          background: C.accent,
                          color: C.bg,
                          fontWeight: 800,
                          fontSize: "0.72rem",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                        }}
                      >
                        {idx + 1}
                      </span>
                      <input
                        type="text"
                        value={p.name}
                        onChange={(e) => handleUpdateName(p.id, e.target.value)}
                        placeholder="Person name..."
                        style={{
                          background: "transparent",
                          border: "none",
                          borderBottom: `1px solid ${C.border}`,
                          color: C.text,
                          fontWeight: 700,
                          fontSize: "0.9rem",
                          outline: "none",
                          padding: "2px 4px",
                        }}
                      />
                    </div>
                    {participants.length > 2 && (
                      <button
                        onClick={() => handleRemoveParticipant(p.id)}
                        style={{
                          background: "none",
                          border: "none",
                          color: C.muted,
                          cursor: "pointer",
                          padding: 4,
                        }}
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>

                  {/* Genre Chips */}
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 6 }}>
                    {POPULAR_GENRES.map((g) => {
                      const active = p.genres.includes(g);
                      return (
                        <button
                          key={g}
                          onClick={() => handleToggleGenre(p.id, g)}
                          style={{
                            background: active ? C.accent : "rgba(255,255,255,0.04)",
                            color: active ? C.bg : C.muted,
                            border: `1px solid ${active ? C.accent : C.border}`,
                            borderRadius: 99,
                            padding: "2px 9px",
                            fontSize: "0.72rem",
                            fontWeight: active ? 700 : 500,
                            cursor: "pointer",
                            transition: "all 0.15s ease",
                          }}
                        >
                          {g}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            <div style={{ marginTop: 14 }}>
              <button
                onClick={handleFindConsensus}
                disabled={loading}
                style={{
                  width: "100%",
                  background: C.accent,
                  color: C.bg,
                  border: "none",
                  borderRadius: 4,
                  padding: "10px",
                  fontSize: "0.86rem",
                  fontWeight: 700,
                  cursor: loading ? "default" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 8,
                }}
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Finding optimal compromise films...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    Find Group Consensus Movie
                  </>
                )}
              </button>
            </div>
          </div>

          {error && (
            <div
              style={{
                padding: "10px 14px",
                background: "rgba(220,53,69,0.15)",
                color: "#ff858d",
                fontSize: "0.8rem",
                borderRadius: 4,
                marginBottom: 16,
              }}
            >
              {error}
            </div>
          )}

          {/* Results Display */}
          {results && !loading && (
            <div style={{ marginTop: 16 }}>
              {/* Compatibility Banner */}
              <div
                style={{
                  background: C.surfaceHigh,
                  border: `1px solid ${C.border}`,
                  borderRadius: 6,
                  padding: "14px 18px",
                  marginBottom: 18,
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                }}
              >
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: 99,
                    background: C.accentDim,
                    border: `2px solid ${C.accent}`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 900,
                    fontSize: "0.95rem",
                    color: C.accent,
                    flexShrink: 0,
                  }}
                >
                  {results.group_compatibility_score}%
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: "0.78rem", fontWeight: 700, color: C.accent, textTransform: "uppercase" }}>
                    Group Taste Alignment
                  </div>
                  <div style={{ fontSize: "0.82rem", color: C.text, marginTop: 2 }}>
                    {results.explanation}
                  </div>
                </div>
              </div>

              {/* Consensus Movie Cards */}
              <h4
                style={{
                  fontSize: "0.8rem",
                  fontWeight: 700,
                  color: C.muted,
                  letterSpacing: "0.06em",
                  textTransform: "uppercase",
                  marginBottom: 12,
                }}
              >
                Top Compromise Selections (Zero-Misery Order)
              </h4>

              <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 12 }}>
                {results.consensus_recommendations.map((m, idx) => {
                  const norm = normalizeMovie(m);
                  return (
                    <div
                      key={m.id || idx}
                      onClick={() => {
                        onSelectMovieForDrawer?.(norm);
                        onClose();
                      }}
                      style={{
                        background: C.surfaceHigh,
                        border: `1px solid ${C.border}`,
                        borderRadius: 6,
                        padding: 12,
                        display: "flex",
                        gap: 14,
                        alignItems: "center",
                        cursor: "pointer",
                        transition: "all 0.2s ease",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.borderColor = C.accent)}
                      onMouseLeave={(e) => (e.currentTarget.style.borderColor = C.border)}
                    >
                      <img
                        src={norm.poster_url || "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=300"}
                        alt={norm.title}
                        style={{
                          width: 52,
                          height: 76,
                          objectFit: "cover",
                          borderRadius: 4,
                          border: `1px solid ${C.border}`,
                          flexShrink: 0,
                        }}
                      />

                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <span
                            style={{
                              background: C.accentDim,
                              color: C.accent,
                              fontSize: "0.72rem",
                              fontWeight: 700,
                              padding: "2px 6px",
                              borderRadius: 3,
                            }}
                          >
                            Score: {m.compromise_score}/10
                          </span>
                          <span style={{ fontWeight: 700, color: C.text, fontSize: "0.92rem" }}>
                            {norm.title}
                          </span>
                          <span style={{ color: C.muted, fontSize: "0.74rem" }}>
                            ({norm.year})
                          </span>
                        </div>

                        {/* Per-participant satisfaction tags */}
                        {m.appeal_per_participant && (
                          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 6 }}>
                            {Object.entries(m.appeal_per_participant).map(([person, note]) => (
                              <span
                                key={person}
                                style={{
                                  background: "rgba(0,0,0,0.35)",
                                  border: `1px solid ${C.border}`,
                                  borderRadius: 3,
                                  fontSize: "0.7rem",
                                  padding: "2px 6px",
                                  color: C.muted,
                                }}
                              >
                                <strong style={{ color: C.text }}>{person}:</strong> {note}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      <div style={{ color: C.muted }}>
                        <ArrowRight size={16} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
