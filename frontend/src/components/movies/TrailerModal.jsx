import React, { useEffect, useState } from "react";
import { X, Play, Film, ExternalLink, Loader2 } from "lucide-react";
import { C } from "../../constants/theme";

export default function TrailerModal({ isOpen, onClose, movieTitle, videos = [], loading = false }) {
  const [activeVideoIdx, setActiveVideoIdx] = useState(0);

  useEffect(() => {
    setActiveVideoIdx(0);
  }, [movieTitle, videos]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const currentVideo = videos && videos.length > 0 ? videos[activeVideoIdx] : null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 10000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 16,
        background: "rgba(8, 4, 12, 0.9)",
        backdropFilter: "blur(14px)",
        animation: "fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1)",
      }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 880,
          background: C.surface,
          borderRadius: 14,
          border: `1px solid ${C.border}`,
          boxShadow: "0 30px 90px -20px rgba(0, 0, 0, 0.85), 0 0 50px rgba(227, 163, 78, 0.12)",
          overflow: "hidden",
          position: "relative",
        }}
      >
        {/* Film perforation top strip */}
        <div
          className="perf-strip"
          style={{
            height: 12,
            background: "#130E17",
            borderBottom: `1px solid ${C.border}`,
            opacity: 0.7,
          }}
        />

        {/* Header Bar */}
        <div
          style={{
            padding: "16px 22px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            borderBottom: `1px solid ${C.border}`,
            background: "#18131C",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10, overflow: "hidden" }}>
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: "50%",
                background: C.accentDim,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <Play size={14} color={C.accent} style={{ marginLeft: 2 }} />
            </div>
            <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              <span
                style={{
                  fontSize: "0.72rem",
                  color: C.accent,
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                  fontWeight: 600,
                  display: "block",
                }}
              >
                Official Trailer
              </span>
              <h3
                style={{
                  margin: 0,
                  fontSize: "1.15rem",
                  color: C.text,
                  fontFamily: "var(--font-display, inherit)",
                  letterSpacing: "-0.01em",
                }}
              >
                {movieTitle || "Movie Preview"}
              </h3>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {currentVideo?.youtube_url && (
              <a
                href={currentVideo.youtube_url}
                target="_blank"
                rel="noopener noreferrer"
                title="Watch on YouTube"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 5,
                  padding: "6px 12px",
                  borderRadius: 6,
                  border: `1px solid ${C.borderBright}`,
                  background: "rgba(255, 255, 255, 0.04)",
                  color: C.muted,
                  fontSize: "0.78rem",
                  textDecoration: "none",
                  transition: "color 0.2s, border 0.2s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = C.accent;
                  e.currentTarget.style.borderColor = C.accent;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = C.muted;
                  e.currentTarget.style.borderColor = C.borderBright;
                }}
              >
                <span>YouTube</span>
                <ExternalLink size={12} />
              </a>
            )}

            <button
              onClick={onClose}
              style={{
                background: "transparent",
                border: `1px solid ${C.border}`,
                borderRadius: "50%",
                width: 32,
                height: 32,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                color: C.muted,
                transition: "all 0.2s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = C.text)}
              onMouseLeave={(e) => (e.currentTarget.style.color = C.muted)}
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Video Player Container */}
        <div
          style={{
            position: "relative",
            width: "100%",
            paddingTop: "56.25%", // 16:9 Aspect Ratio
            background: "#08060A",
          }}
        >
          {loading ? (
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 12,
                color: C.muted,
              }}
            >
              <Loader2 size={36} className="animate-spin" color={C.accent} />
              <span style={{ fontSize: "0.85rem", letterSpacing: "0.05em" }}>
                Connecting to TMDB video feed...
              </span>
            </div>
          ) : currentVideo?.key ? (
            <iframe
              src={`https://www.youtube-nocookie.com/embed/${currentVideo.key}?autoplay=1&rel=0&modestbranding=1`}
              title={currentVideo.name || `${movieTitle} Trailer`}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              allowFullScreen
              style={{
                position: "absolute",
                inset: 0,
                width: "100%",
                height: "100%",
                border: "none",
              }}
            />
          ) : (
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 12,
                color: C.muted,
                padding: 24,
                textAlign: "center",
              }}
            >
              <Film size={42} color={C.borderBright} />
              <p style={{ margin: 0, fontSize: "0.95rem", color: C.text }}>
                No video trailer available for this title on TMDB.
              </p>
              <span style={{ fontSize: "0.8rem", color: C.muted }}>
                Check back shortly or search title directly on official film distributors.
              </span>
            </div>
          )}
        </div>

        {/* Video switcher tabs if multiple trailers exist */}
        {videos && videos.length > 1 && (
          <div
            style={{
              padding: "12px 18px",
              background: "#16111A",
              borderTop: `1px solid ${C.border}`,
              display: "flex",
              alignItems: "center",
              gap: 8,
              overflowX: "auto",
            }}
          >
            <span
              style={{
                fontSize: "0.72rem",
                color: C.muted,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                marginRight: 6,
                flexShrink: 0,
              }}
            >
              Clips ({videos.length}):
            </span>
            {videos.slice(0, 5).map((v, idx) => (
              <button
                key={v.id || idx}
                onClick={() => setActiveVideoIdx(idx)}
                style={{
                  padding: "5px 12px",
                  borderRadius: 20,
                  fontSize: "0.75rem",
                  fontWeight: activeVideoIdx === idx ? 700 : 500,
                  background: activeVideoIdx === idx ? C.accentDim : "rgba(255,255,255,0.04)",
                  color: activeVideoIdx === idx ? C.accent : C.muted,
                  border: `1px solid ${activeVideoIdx === idx ? C.accent : C.border}`,
                  cursor: "pointer",
                  whiteSpace: "nowrap",
                  transition: "all 0.15s",
                }}
              >
                {v.type || "Trailer"} {idx + 1}: {v.name ? (v.name.length > 25 ? v.name.slice(0, 22) + "..." : v.name) : ""}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
