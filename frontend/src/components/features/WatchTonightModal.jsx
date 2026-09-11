import React, { useState } from "react";
import {
  X,
  Compass,
  Clock,
  Sparkles,
  Users,
  Globe,
  ArrowRight,
  RotateCcw,
  Star,
  Film,
  Check,
  Loader2,
} from "lucide-react";
import { C } from "../../constants/theme";
import { getWatchTonightRecs } from "../../api/client";
import { normalizeMovie } from "../../utils/normalizers";

const TIME_OPTIONS = [
  { id: "quick", title: "Quick Snack", desc: "< 95 min • Fast & punchy", icon: Clock },
  { id: "standard", title: "Prime Feature", desc: "95–125 min • Classic film night", icon: Film },
  { id: "epic", title: "Cinematic Epic", desc: "> 125 min • Deep immersion", icon: Compass },
];

const MOOD_OPTIONS = [
  { id: "thrilling", title: "Adrenaline Rush", desc: "Edge-of-seat action & suspense", emoji: "⚡" },
  { id: "feel_good", title: "Laugh & Chill", desc: "Heartwarming comedy & fun", emoji: "✨" },
  { id: "mind_bending", title: "Mind-Bender", desc: "Cerebral sci-fi & twisted plots", emoji: "🌀" },
  { id: "deep", title: "Deep & Soulful", desc: "Emotional storytelling & drama", emoji: "🎭" },
  { id: "scary", title: "Spine Chiller", desc: "Dark tension & horror thrill", emoji: "👻" },
];

const COMPANY_OPTIONS = [
  { id: "solo", title: "Solo Mission", desc: "Undivided focus, no compromises", icon: "👤" },
  { id: "date_night", title: "Date Night", desc: "Engaging, stylish & fun", icon: "🍷" },
  { id: "friends", title: "Friend Squad", desc: "Crowd-pleasers & lively energy", icon: "🍿" },
  { id: "family", title: "Family Gathering", desc: "Wholesome & universally enjoyed", icon: "🏡" },
];

const LANG_OPTIONS = [
  { id: "any", label: "World Cinema (Any)" },
  { id: "en", label: "English" },
  { id: "hi", label: "Hindi (Bollywood)" },
  { id: "mr", label: "Marathi Cinema" },
  { id: "te", label: "Telugu Cinema" },
  { id: "ta", label: "Tamil Cinema" },
];

export default function WatchTonightModal({
  isOpen,
  onClose,
  onSelectMovieForDrawer,
}) {
  const [step, setStep] = useState(1);
  const [time, setTime] = useState("standard");
  const [mood, setMood] = useState("thrilling");
  const [company, setCompany] = useState("solo");
  const [language, setLanguage] = useState("any");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getWatchTonightRecs({
        available_time: time,
        mood,
        company,
        language,
      });
      setResult(data);
      setStep(5); // Results view
    } catch {
      setError("Failed to fetch tonight's recommendations. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStep(1);
    setResult(null);
    setError(null);
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
          maxWidth: "46rem",
          maxHeight: "90vh",
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
              <Compass size={18} color={C.accent} />
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
                WHAT SHOULD I WATCH TONIGHT?
              </h2>
              <p style={{ fontSize: "0.78rem", color: C.muted }}>
                {step <= 4 ? `Step ${step} of 4 • Curating your evening` : "Tonight's Tailored Lineup"}
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

        {/* Progress Bar (if in wizard mode) */}
        {step <= 4 && (
          <div style={{ height: 3, background: C.border, width: "100%" }}>
            <div
              style={{
                height: "100%",
                background: C.accent,
                width: `${(step / 4) * 100}%`,
                transition: "width 0.3s ease",
              }}
            />
          </div>
        )}

        {/* Body */}
        <div style={{ padding: "24px", overflowY: "auto", flex: 1 }}>
          {/* ── STEP 1: Available Time ── */}
          {step === 1 && (
            <div>
              <div style={{ marginBottom: 18 }}>
                <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: C.text }}>
                  How much time do you have tonight?
                </h3>
                <p style={{ fontSize: "0.82rem", color: C.muted }}>
                  We'll constrain movie runtimes to match your schedule.
                </p>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 12 }}>
                {TIME_OPTIONS.map((opt) => {
                  const Icon = opt.icon;
                  const selected = time === opt.id;
                  return (
                    <div
                      key={opt.id}
                      onClick={() => setTime(opt.id)}
                      style={{
                        padding: "16px 18px",
                        borderRadius: 6,
                        background: selected ? C.accentDim : C.surfaceHigh,
                        border: `1px solid ${selected ? C.accent : C.border}`,
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        transition: "all 0.2s ease",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                        <div
                          style={{
                            width: 36,
                            height: 36,
                            borderRadius: 99,
                            background: selected ? C.accent : "rgba(255,255,255,0.05)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                          }}
                        >
                          <Icon size={18} color={selected ? C.bg : C.text} />
                        </div>
                        <div>
                          <div style={{ fontWeight: 700, color: C.text, fontSize: "0.95rem" }}>
                            {opt.title}
                          </div>
                          <div style={{ fontSize: "0.78rem", color: C.muted }}>{opt.desc}</div>
                        </div>
                      </div>
                      {selected && <Check size={18} color={C.accent} />}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── STEP 2: The Mood ── */}
          {step === 2 && (
            <div>
              <div style={{ marginBottom: 18 }}>
                <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: C.text }}>
                  What's the energy / vibe you want?
                </h3>
                <p style={{ fontSize: "0.82rem", color: C.muted }}>
                  Select the feeling that best matches tonight's state of mind.
                </p>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                {MOOD_OPTIONS.map((opt) => {
                  const selected = mood === opt.id;
                  return (
                    <div
                      key={opt.id}
                      onClick={() => setMood(opt.id)}
                      style={{
                        padding: "14px 16px",
                        borderRadius: 6,
                        background: selected ? C.accentDim : C.surfaceHigh,
                        border: `1px solid ${selected ? C.accent : C.border}`,
                        cursor: "pointer",
                        display: "flex",
                        flexDirection: "column",
                        gap: 6,
                        transition: "all 0.2s ease",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontSize: "1.4rem" }}>{opt.emoji}</span>
                        {selected && <Check size={16} color={C.accent} />}
                      </div>
                      <div style={{ fontWeight: 700, color: C.text, fontSize: "0.9rem" }}>
                        {opt.title}
                      </div>
                      <div style={{ fontSize: "0.76rem", color: C.muted, lineHeight: 1.3 }}>
                        {opt.desc}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── STEP 3: Company ── */}
          {step === 3 && (
            <div>
              <div style={{ marginBottom: 18 }}>
                <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: C.text }}>
                  Who's watching with you?
                </h3>
                <p style={{ fontSize: "0.82rem", color: C.muted }}>
                  We'll tune tone, pacing, and crowd appeal accordingly.
                </p>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                {COMPANY_OPTIONS.map((opt) => {
                  const selected = company === opt.id;
                  return (
                    <div
                      key={opt.id}
                      onClick={() => setCompany(opt.id)}
                      style={{
                        padding: "14px 16px",
                        borderRadius: 6,
                        background: selected ? C.accentDim : C.surfaceHigh,
                        border: `1px solid ${selected ? C.accent : C.border}`,
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: 12,
                        transition: "all 0.2s ease",
                      }}
                    >
                      <span style={{ fontSize: "1.5rem" }}>{opt.icon}</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 700, color: C.text, fontSize: "0.9rem" }}>
                          {opt.title}
                        </div>
                        <div style={{ fontSize: "0.75rem", color: C.muted }}>{opt.desc}</div>
                      </div>
                      {selected && <Check size={16} color={C.accent} />}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── STEP 4: Language & Cinema ── */}
          {step === 4 && (
            <div>
              <div style={{ marginBottom: 18 }}>
                <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: C.text }}>
                  Any language preference?
                </h3>
                <p style={{ fontSize: "0.82rem", color: C.muted }}>
                  Explore global cinema or zero in on your favorite regional industry.
                </p>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                {LANG_OPTIONS.map((opt) => {
                  const selected = language === opt.id;
                  return (
                    <div
                      key={opt.id}
                      onClick={() => setLanguage(opt.id)}
                      style={{
                        padding: "12px 14px",
                        borderRadius: 6,
                        background: selected ? C.accentDim : C.surfaceHigh,
                        border: `1px solid ${selected ? C.accent : C.border}`,
                        cursor: "pointer",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        fontSize: "0.85rem",
                        color: C.text,
                        fontWeight: selected ? 700 : 500,
                      }}
                    >
                      <span>{opt.label}</span>
                      {selected && <Check size={16} color={C.accent} />}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── STEP 5: Results ── */}
          {step === 5 && result && (
            <div>
              <div
                style={{
                  background: "rgba(227,163,78,0.08)",
                  border: `1px solid rgba(227,163,78,0.25)`,
                  borderRadius: 6,
                  padding: "12px 16px",
                  marginBottom: 20,
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                }}
              >
                <Sparkles size={18} color={C.accent} />
                <span style={{ fontSize: "0.85rem", color: C.text, fontWeight: 600 }}>
                  {result.night_vibe_summary}
                </span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {result.recommendations.map((m, idx) => {
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
                        gap: 16,
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
                          width: 58,
                          height: 84,
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
                              background: C.accent,
                              color: C.bg,
                              borderRadius: 99,
                              fontWeight: 800,
                              fontSize: "0.68rem",
                              padding: "1px 7px",
                            }}
                          >
                            #{idx + 1} PICK
                          </span>
                          <h4
                            style={{
                              fontSize: "0.98rem",
                              fontWeight: 700,
                              color: C.text,
                              whiteSpace: "nowrap",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                            }}
                          >
                            {norm.title}
                          </h4>
                        </div>
                        <div style={{ fontSize: "0.76rem", color: C.muted, marginTop: 4 }}>
                          {norm.year} • {norm.runtime ? `${norm.runtime}m` : "110m"} • ★ {norm.rating} • {norm.genres.slice(0, 2).join(", ")}
                        </div>
                        <div
                          style={{
                            fontSize: "0.78rem",
                            color: C.accent,
                            marginTop: 6,
                            lineHeight: 1.35,
                          }}
                        >
                          {m.reason}
                        </div>
                      </div>
                      <div style={{ color: C.muted }}>
                        <ArrowRight size={18} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {error && (
            <div
              style={{
                marginTop: 14,
                padding: "10px 14px",
                background: "rgba(220,53,69,0.15)",
                color: "#ff858d",
                fontSize: "0.8rem",
                borderRadius: 4,
              }}
            >
              {error}
            </div>
          )}
        </div>

        {/* Footer Navigation */}
        <div
          style={{
            padding: "14px 24px",
            borderTop: `1px solid ${C.border}`,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            background: C.surfaceHigh,
          }}
        >
          {step > 1 && step <= 4 ? (
            <button
              onClick={() => setStep((s) => s - 1)}
              style={{
                background: "none",
                border: "none",
                color: C.muted,
                fontSize: "0.82rem",
                cursor: "pointer",
              }}
            >
              Back
            </button>
          ) : step === 5 ? (
            <button
              onClick={handleReset}
              style={{
                background: "none",
                border: `1px solid ${C.border}`,
                color: C.muted,
                padding: "6px 12px",
                borderRadius: 4,
                fontSize: "0.8rem",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <RotateCcw size={14} />
              Try Another Vibe
            </button>
          ) : (
            <div />
          )}

          {step < 4 ? (
            <button
              onClick={() => setStep((s) => s + 1)}
              style={{
                background: C.accent,
                color: C.bg,
                border: "none",
                borderRadius: 4,
                padding: "8px 18px",
                fontSize: "0.82rem",
                fontWeight: 700,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              Next
              <ArrowRight size={14} />
            </button>
          ) : step === 4 ? (
            <button
              onClick={handleGenerate}
              disabled={loading}
              style={{
                background: C.accent,
                color: C.bg,
                border: "none",
                borderRadius: 4,
                padding: "8px 20px",
                fontSize: "0.85rem",
                fontWeight: 700,
                cursor: loading ? "default" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Finding perfect films...
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  Reveal Tonight's Movies
                </>
              )}
            </button>
          ) : (
            <button
              onClick={onClose}
              style={{
                background: C.surface,
                border: `1px solid ${C.border}`,
                color: C.text,
                borderRadius: 4,
                padding: "6px 14px",
                fontSize: "0.8rem",
                cursor: "pointer",
              }}
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
