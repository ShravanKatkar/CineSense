import React, { useState, useEffect, useRef } from "react";
import {
  X,
  Scale,
  Sparkles,
  Search,
  Check,
  ChevronRight,
  Flame,
  Clock,
  Star,
  Film,
  ArrowRightLeft,
  Loader2,
} from "lucide-react";
import { C } from "../../constants/theme";
import { compareMovies, searchMovies } from "../../api/client";
import { normalizeMovie } from "../../utils/normalizers";

const QUICK_PICKS = [
  { id: 1, title: "Toy Story", year: 1995 },
  { id: 260, title: "Star Wars", year: 1977 },
  { id: 296, title: "Pulp Fiction", year: 1994 },
  { id: 356, title: "Forrest Gump", year: 1994 },
  { id: 2571, title: "The Matrix", year: 1999 },
];

const METRIC_LABELS = [
  { key: "pacing", label: "Pacing & Tempo", desc: "Energy rhythm & editing drive" },
  { key: "visual_spectacle", label: "Visual Scope", desc: "CGI, cinematography & worldbuilding" },
  { key: "emotional_depth", label: "Emotional Resonance", desc: "Character intimacy & weight" },
  { key: "story_complexity", label: "Narrative Complexity", desc: "Plot intrigue & thematic layers" },
  { key: "rewatchability", label: "Rewatchability", desc: "Long-term crowd appeal" },
];

export default function MovieComparisonModal({
  isOpen,
  onClose,
  initialMovieA = null,
  initialMovieB = null,
  onSelectMovieForDrawer,
}) {
  const [movieA, setMovieA] = useState(initialMovieA);
  const [movieB, setMovieB] = useState(initialMovieB);

  const [queryA, setQueryA] = useState("");
  const [queryB, setQueryB] = useState("");
  const [resultsA, setResultsA] = useState([]);
  const [resultsB, setResultsB] = useState([]);
  const [searchingA, setSearchingA] = useState(false);
  const [searchingB, setSearchingB] = useState(false);

  const [comparing, setComparing] = useState(false);
  const [compareData, setCompareData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (initialMovieA) setMovieA(initialMovieA);
  }, [initialMovieA]);

  useEffect(() => {
    if (initialMovieB) setMovieB(initialMovieB);
  }, [initialMovieB]);

  // Autocomplete search for Movie A
  useEffect(() => {
    if (!queryA.trim() || queryA.length < 2) {
      setResultsA([]);
      return;
    }
    let cancelled = false;
    const t = setTimeout(async () => {
      setSearchingA(true);
      try {
        const res = await searchMovies(queryA);
        if (!cancelled) setResultsA((res || []).slice(0, 5));
      } catch {
        if (!cancelled) setResultsA([]);
      } finally {
        if (!cancelled) setSearchingA(false);
      }
    }, 280);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [queryA]);

  // Autocomplete search for Movie B
  useEffect(() => {
    if (!queryB.trim() || queryB.length < 2) {
      setResultsB([]);
      return;
    }
    let cancelled = false;
    const t = setTimeout(async () => {
      setSearchingB(true);
      try {
        const res = await searchMovies(queryB);
        if (!cancelled) setResultsB((res || []).slice(0, 5));
      } catch {
        if (!cancelled) setResultsB([]);
      } finally {
        if (!cancelled) setSearchingB(false);
      }
    }, 280);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [queryB]);

  // Run comparison whenever both movies are set
  const handleCompare = async () => {
    if (!movieA || !movieB) return;
    setComparing(true);
    setError(null);
    try {
      const data = await compareMovies(movieA.id, movieB.id);
      setCompareData(data);
    } catch (err) {
      setError("Unable to compare movies right now. Please verify selection.");
    } finally {
      setComparing(false);
    }
  };

  useEffect(() => {
    if (movieA && movieB && isOpen) {
      handleCompare();
    }
  }, [movieA?.id, movieB?.id, isOpen]);

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
          maxWidth: "58rem",
          maxHeight: "92vh",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          boxShadow: "0 24px 60px rgba(0,0,0,0.8)",
          position: "relative",
        }}
      >
        {/* Top Header */}
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
              <ArrowRightLeft size={18} color={C.accent} />
            </div>
            <div>
              <h2
                className="font-display"
                style={{
                  fontSize: "1.4rem",
                  color: C.text,
                  letterSpacing: "-0.01em",
                  lineHeight: 1.1,
                }}
              >
                HEAD-TO-HEAD MOVIE COMPARISON
              </h2>
              <p style={{ fontSize: "0.78rem", color: C.muted }}>
                Algorithmic dimension scoring & AI tradeoff synthesis
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
              borderRadius: 4,
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ overflowY: "auto", padding: "22px 24px", flex: 1 }}>
          {/* Movie Selectors Grid */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr auto 1fr",
              gap: 16,
              alignItems: "start",
              marginBottom: 24,
            }}
          >
            {/* Slot A */}
            <div
              style={{
                background: "rgba(20,16,24,0.6)",
                border: `1px solid ${movieA ? C.accent : C.border}`,
                borderRadius: 6,
                padding: 16,
                position: "relative",
              }}
            >
              <div
                style={{
                  fontSize: "0.72rem",
                  fontWeight: 700,
                  color: C.accent,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  marginBottom: 8,
                }}
              >
                Film A
              </div>

              {movieA ? (
                <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                  <img
                    src={movieA.poster_url || "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=300"}
                    alt={movieA.title}
                    style={{
                      width: 52,
                      height: 76,
                      objectFit: "cover",
                      borderRadius: 4,
                      border: `1px solid ${C.border}`,
                    }}
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        fontWeight: 700,
                        color: C.text,
                        fontSize: "0.95rem",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {movieA.title}
                    </div>
                    <div style={{ fontSize: "0.76rem", color: C.muted, marginTop: 2 }}>
                      {String(movieA.release_date || movieA.year || "2020").slice(0, 4)} • {movieA.runtime ? `${movieA.runtime}m` : "110m"} • ★ {movieA.vote_average || 7.5}
                    </div>
                    <button
                      onClick={() => {
                        setMovieA(null);
                        setCompareData(null);
                      }}
                      style={{
                        background: "none",
                        border: "none",
                        color: C.accent,
                        fontSize: "0.72rem",
                        cursor: "pointer",
                        padding: 0,
                        marginTop: 6,
                        textDecoration: "underline",
                      }}
                    >
                      Change selection
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{ position: "relative" }}>
                    <Search
                      size={14}
                      color={C.muted}
                      style={{ position: "absolute", left: 10, top: 11 }}
                    />
                    <input
                      type="text"
                      placeholder="Search title (e.g. Inception)..."
                      value={queryA}
                      onChange={(e) => setQueryA(e.target.value)}
                      style={{
                        width: "100%",
                        background: C.surfaceHigh,
                        border: `1px solid ${C.border}`,
                        borderRadius: 4,
                        padding: "8px 12px 8px 32px",
                        color: C.text,
                        fontSize: "0.82rem",
                        outline: "none",
                      }}
                    />
                  </div>

                  {/* Autocomplete dropdown A */}
                  {resultsA.length > 0 && (
                    <div
                      style={{
                        marginTop: 6,
                        background: C.surfaceHigh,
                        border: `1px solid ${C.borderBright}`,
                        borderRadius: 4,
                        overflow: "hidden",
                      }}
                    >
                      {resultsA.map((r) => (
                        <div
                          key={r.id}
                          onClick={() => {
                            setMovieA(normalizeMovie(r));
                            setQueryA("");
                            setResultsA([]);
                          }}
                          style={{
                            padding: "6px 10px",
                            fontSize: "0.8rem",
                            cursor: "pointer",
                            color: C.text,
                            borderBottom: `1px solid ${C.border}`,
                            display: "flex",
                            justifyContent: "space-between",
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.background = C.surface)}
                          onMouseLeave={(e) => (e.currentTarget.style.background = C.surfaceHigh)}
                        >
                          <span style={{ fontWeight: 600 }}>{r.title}</span>
                          <span style={{ color: C.muted, fontSize: "0.72rem" }}>
                            {String(r.release_date || "").slice(0, 4)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Quick Suggestions A */}
                  <div style={{ marginTop: 8, display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {QUICK_PICKS.slice(0, 3).map((p) => (
                      <button
                        key={p.id}
                        onClick={() => setMovieA(p)}
                        style={{
                          background: C.surfaceHigh,
                          border: `1px solid ${C.border}`,
                          color: C.muted,
                          fontSize: "0.7rem",
                          borderRadius: 3,
                          padding: "3px 7px",
                          cursor: "pointer",
                        }}
                      >
                        {p.title}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* VS Divider */}
            <div
              style={{
                alignSelf: "center",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 4,
              }}
            >
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: 99,
                  background: C.surfaceHigh,
                  border: `1px solid ${C.border}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 800,
                  fontSize: "0.82rem",
                  color: C.accent,
                }}
              >
                VS
              </div>
            </div>

            {/* Slot B */}
            <div
              style={{
                background: "rgba(20,16,24,0.6)",
                border: `1px solid ${movieB ? C.teal : C.border}`,
                borderRadius: 6,
                padding: 16,
                position: "relative",
              }}
            >
              <div
                style={{
                  fontSize: "0.72rem",
                  fontWeight: 700,
                  color: C.teal,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  marginBottom: 8,
                }}
              >
                Film B
              </div>

              {movieB ? (
                <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                  <img
                    src={movieB.poster_url || "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=300"}
                    alt={movieB.title}
                    style={{
                      width: 52,
                      height: 76,
                      objectFit: "cover",
                      borderRadius: 4,
                      border: `1px solid ${C.border}`,
                    }}
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        fontWeight: 700,
                        color: C.text,
                        fontSize: "0.95rem",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {movieB.title}
                    </div>
                    <div style={{ fontSize: "0.76rem", color: C.muted, marginTop: 2 }}>
                      {String(movieB.release_date || movieB.year || "2020").slice(0, 4)} • {movieB.runtime ? `${movieB.runtime}m` : "110m"} • ★ {movieB.vote_average || 7.5}
                    </div>
                    <button
                      onClick={() => {
                        setMovieB(null);
                        setCompareData(null);
                      }}
                      style={{
                        background: "none",
                        border: "none",
                        color: C.teal,
                        fontSize: "0.72rem",
                        cursor: "pointer",
                        padding: 0,
                        marginTop: 6,
                        textDecoration: "underline",
                      }}
                    >
                      Change selection
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{ position: "relative" }}>
                    <Search
                      size={14}
                      color={C.muted}
                      style={{ position: "absolute", left: 10, top: 11 }}
                    />
                    <input
                      type="text"
                      placeholder="Search title (e.g. Interstellar)..."
                      value={queryB}
                      onChange={(e) => setQueryB(e.target.value)}
                      style={{
                        width: "100%",
                        background: C.surfaceHigh,
                        border: `1px solid ${C.border}`,
                        borderRadius: 4,
                        padding: "8px 12px 8px 32px",
                        color: C.text,
                        fontSize: "0.82rem",
                        outline: "none",
                      }}
                    />
                  </div>

                  {/* Autocomplete dropdown B */}
                  {resultsB.length > 0 && (
                    <div
                      style={{
                        marginTop: 6,
                        background: C.surfaceHigh,
                        border: `1px solid ${C.borderBright}`,
                        borderRadius: 4,
                        overflow: "hidden",
                      }}
                    >
                      {resultsB.map((r) => (
                        <div
                          key={r.id}
                          onClick={() => {
                            setMovieB(normalizeMovie(r));
                            setQueryB("");
                            setResultsB([]);
                          }}
                          style={{
                            padding: "6px 10px",
                            fontSize: "0.8rem",
                            cursor: "pointer",
                            color: C.text,
                            borderBottom: `1px solid ${C.border}`,
                            display: "flex",
                            justifyContent: "space-between",
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.background = C.surface)}
                          onMouseLeave={(e) => (e.currentTarget.style.background = C.surfaceHigh)}
                        >
                          <span style={{ fontWeight: 600 }}>{r.title}</span>
                          <span style={{ color: C.muted, fontSize: "0.72rem" }}>
                            {String(r.release_date || "").slice(0, 4)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Quick Suggestions B */}
                  <div style={{ marginTop: 8, display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {QUICK_PICKS.slice(2, 5).map((p) => (
                      <button
                        key={p.id}
                        onClick={() => setMovieB(p)}
                        style={{
                          background: C.surfaceHigh,
                          border: `1px solid ${C.border}`,
                          color: C.muted,
                          fontSize: "0.7rem",
                          borderRadius: 3,
                          padding: "3px 7px",
                          cursor: "pointer",
                        }}
                      >
                        {p.title}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Comparing State */}
          {comparing && (
            <div
              style={{
                padding: "36px 0",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 12,
              }}
            >
              <Loader2 size={28} color={C.accent} className="animate-spin" />
              <div style={{ fontSize: "0.88rem", color: C.muted }}>
                Comparing narrative dimensions & consulting AI critic...
              </div>
            </div>
          )}

          {error && (
            <div
              style={{
                padding: "12px 16px",
                background: "rgba(220,53,69,0.15)",
                border: "1px solid rgba(220,53,69,0.4)",
                color: "#ff858d",
                fontSize: "0.82rem",
                borderRadius: 4,
                marginBottom: 16,
              }}
            >
              {error}
            </div>
          )}

          {/* Comparison Results */}
          {compareData && !comparing && (
            <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
              {/* Comparative Dimensions */}
              <div
                style={{
                  background: C.surfaceHigh,
                  border: `1px solid ${C.border}`,
                  borderRadius: 6,
                  padding: "18px 20px",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 16,
                  }}
                >
                  <h3
                    style={{
                      fontSize: "0.86rem",
                      fontWeight: 700,
                      color: C.text,
                      letterSpacing: "0.04em",
                      textTransform: "uppercase",
                    }}
                  >
                    Cinematic Dimensions (Scale 1–10)
                  </h3>
                  <div style={{ display: "flex", gap: 16, fontSize: "0.75rem" }}>
                    <span style={{ color: C.accent, fontWeight: 600 }}>● {compareData.movie_a.title}</span>
                    <span style={{ color: C.teal, fontWeight: 600 }}>● {compareData.movie_b.title}</span>
                  </div>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                  {METRIC_LABELS.map(({ key, label, desc }) => {
                    const scoreA = compareData.metrics_a[key] || 5;
                    const scoreB = compareData.metrics_b[key] || 5;
                    return (
                      <div key={key}>
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            fontSize: "0.78rem",
                            marginBottom: 4,
                          }}
                        >
                          <span style={{ color: C.text, fontWeight: 600 }}>
                            {label}{" "}
                            <span style={{ color: C.muted, fontWeight: 400 }}>({desc})</span>
                          </span>
                          <span style={{ fontSize: "0.74rem" }}>
                            <strong style={{ color: C.accent }}>{scoreA}</strong> vs{" "}
                            <strong style={{ color: C.teal }}>{scoreB}</strong>
                          </span>
                        </div>

                        {/* Comparative Dual Bar */}
                        <div
                          style={{
                            display: "grid",
                            gridTemplateColumns: "1fr 1fr",
                            gap: 6,
                            height: 8,
                          }}
                        >
                          {/* Slot A (grows right to left) */}
                          <div
                            style={{
                              background: "rgba(0,0,0,0.3)",
                              borderRadius: 3,
                              overflow: "hidden",
                              display: "flex",
                              justifyContent: "flex-end",
                            }}
                          >
                            <div
                              style={{
                                width: `${(scoreA / 10) * 100}%`,
                                background: C.accent,
                                height: "100%",
                                borderRadius: 3,
                                transition: "width 0.5s ease",
                              }}
                            />
                          </div>

                          {/* Slot B (grows left to right) */}
                          <div
                            style={{
                              background: "rgba(0,0,0,0.3)",
                              borderRadius: 3,
                              overflow: "hidden",
                            }}
                          >
                            <div
                              style={{
                                width: `${(scoreB / 10) * 100}%`,
                                background: C.teal,
                                height: "100%",
                                borderRadius: 3,
                                transition: "width 0.5s ease",
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Tradeoff Breakdown */}
              {compareData.tradeoffs?.length > 0 && (
                <div
                  style={{
                    background: "rgba(227,163,78,0.06)",
                    border: `1px solid rgba(227,163,78,0.25)`,
                    borderRadius: 6,
                    padding: "16px 20px",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      fontSize: "0.8rem",
                      fontWeight: 700,
                      color: C.accent,
                      textTransform: "uppercase",
                      letterSpacing: "0.06em",
                      marginBottom: 10,
                    }}
                  >
                    <Sparkles size={14} color={C.accent} />
                    Critical Tradeoffs
                  </div>
                  <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
                    {compareData.tradeoffs.map((t, idx) => (
                      <li
                        key={idx}
                        style={{
                          fontSize: "0.82rem",
                          color: C.text,
                          lineHeight: 1.45,
                          display: "flex",
                          gap: 8,
                        }}
                      >
                        <span style={{ color: C.accent }}>▸</span>
                        <span dangerouslySetInnerHTML={{ __html: t.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Mood Recommendations */}
              {compareData.winner_for_mood && Object.keys(compareData.winner_for_mood).length > 0 && (
                <div>
                  <h4
                    style={{
                      fontSize: "0.78rem",
                      fontWeight: 700,
                      color: C.muted,
                      letterSpacing: "0.06em",
                      textTransform: "uppercase",
                      marginBottom: 10,
                    }}
                  >
                    Which one fits your mood tonight?
                  </h4>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 10 }}>
                    {Object.entries(compareData.winner_for_mood).map(([mood, filmTitle]) => {
                      const isA = filmTitle.toLowerCase().includes(compareData.movie_a.title.toLowerCase());
                      return (
                        <div
                          key={mood}
                          style={{
                            background: C.surfaceHigh,
                            border: `1px solid ${isA ? C.accentDim : "rgba(79,124,116,0.3)"}`,
                            borderRadius: 4,
                            padding: "10px 14px",
                          }}
                        >
                          <div style={{ fontSize: "0.72rem", color: C.muted, textTransform: "uppercase" }}>
                            {mood}
                          </div>
                          <div
                            style={{
                              fontSize: "0.88rem",
                              fontWeight: 700,
                              color: isA ? C.accent : C.teal,
                              marginTop: 2,
                            }}
                          >
                            👉 {filmTitle}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Bottom Line Verdict */}
              {compareData.ai_verdict && (
                <div
                  style={{
                    background: C.surfaceHigh,
                    borderLeft: `4px solid ${C.accent}`,
                    padding: "14px 18px",
                    borderRadius: "0 6px 6px 0",
                  }}
                >
                  <div
                    style={{
                      fontSize: "0.74rem",
                      fontWeight: 700,
                      color: C.accent,
                      textTransform: "uppercase",
                      letterSpacing: "0.06em",
                      marginBottom: 4,
                    }}
                  >
                    The Curator's Verdict
                  </div>
                  <p style={{ fontSize: "0.85rem", color: C.text, lineHeight: 1.5 }}>
                    {compareData.ai_verdict}
                  </p>
                </div>
              )}

              {/* Action Buttons to open full drawers */}
              <div style={{ display: "flex", gap: 12, justifyContent: "flex-end", marginTop: 4 }}>
                <button
                  onClick={() => {
                    onSelectMovieForDrawer?.(compareData.movie_a);
                    onClose();
                  }}
                  style={{
                    background: "none",
                    border: `1px solid ${C.accent}`,
                    color: C.accent,
                    borderRadius: 4,
                    padding: "7px 14px",
                    fontSize: "0.8rem",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Explore {compareData.movie_a.title}
                </button>
                <button
                  onClick={() => {
                    onSelectMovieForDrawer?.(compareData.movie_b);
                    onClose();
                  }}
                  style={{
                    background: "none",
                    border: `1px solid ${C.teal}`,
                    color: C.teal,
                    borderRadius: 4,
                    padding: "7px 14px",
                    fontSize: "0.8rem",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Explore {compareData.movie_b.title}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
