import React from "react";
import { Star, Film, Heart, ChevronRight } from "lucide-react";
import { C } from "../../constants/theme";
import AnimatedTitle from "../common/AnimatedTitle";

export default function BillboardHero({
  featured,
  heroReady,
  liked,
  onToggleLike,
  onOpenDetails,
}) {
  if (!featured) return null;

  const bgUrl = featured.backdrop_url || featured.poster_url;

  return (
    <section
      style={{
        position: "relative",
        width: "100%",
        minHeight: "70vh",
        overflow: "hidden",
        display: "flex",
        alignItems: "flex-end",
      }}
    >
      {/* Billboard background image */}
      {bgUrl && (
        <img
          src={bgUrl}
          alt={featured.title}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: "center top",
            zIndex: 0,
          }}
        />
      )}

      {/* Dark gradient overlays for readability */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          zIndex: 1,
          background: `linear-gradient(to top, ${C.bg} 0%, ${C.bg}ee 20%, ${C.bg}99 45%, ${C.bg}44 70%, ${C.bg}22 100%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          zIndex: 1,
          background: `linear-gradient(to right, ${C.bg}dd 0%, ${C.bg}88 40%, transparent 70%)`,
        }}
      />

      {/* Film grain on top of image */}
      <div className="grain-overlay" style={{ zIndex: 2 }} />

      {/* Content overlay */}
      <div
        style={{
          position: "relative",
          zIndex: 3,
          maxWidth: "80rem",
          margin: "0 auto",
          padding: "4rem 1.5rem 3rem",
          width: "100%",
        }}
      >
        <div
          className={heroReady ? "hero-reveal" : ""}
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "flex-end",
            opacity: heroReady ? 1 : 0,
            maxWidth: 640,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
            <div className="accent-line" />
            <span
              style={{
                fontSize: "0.78rem",
                color: C.muted,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
              }}
            >
              Tonight's Feature
            </span>
          </div>

          <h1
            className="font-display"
            style={{
              fontSize: "clamp(3rem, 7vw, 5.5rem)",
              lineHeight: 0.93,
              color: C.text,
              letterSpacing: "-0.03em",
              marginBottom: 20,
            }}
          >
            <AnimatedTitle text={featured.title || ""} ready={heroReady} />
          </h1>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              fontSize: "0.85rem",
              color: C.muted,
              marginBottom: 12,
              flexWrap: "wrap",
            }}
          >
            <span style={{ fontWeight: 600, color: C.text }}>{featured.year}</span>
            <span style={{ width: 1, height: 12, background: C.border, display: "inline-block" }} />
            <span>{featured.runtime || 110} min</span>
            <span style={{ width: 1, height: 12, background: C.border, display: "inline-block" }} />
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <Star size={13} fill={C.accent} color={C.accent} />
              <span style={{ fontWeight: 700, color: C.accent }}>{featured.rating}</span>
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <Film size={13} color={C.muted} />
              {featured.director}
            </span>
          </div>

          <p
            style={{
              fontSize: "0.78rem",
              color: C.teal,
              fontStyle: "italic",
              marginBottom: 14,
              letterSpacing: "0.04em",
            }}
          >
            {featured.genres?.join("  ·  ")}
          </p>

          <p
            style={{
              fontSize: "0.95rem",
              lineHeight: 1.7,
              color: C.muted,
              maxWidth: 480,
              marginBottom: 28,
              display: "-webkit-box",
              WebkitLineClamp: 3,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}
          >
            {featured.blurb}
          </p>

          <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
            <button
              onClick={() => onToggleLike(featured)}
              className="cta-btn"
              style={{
                background: C.accent,
                color: C.bg,
                border: "none",
                padding: "11px 24px",
                fontSize: "0.875rem",
                fontWeight: 700,
                fontFamily: "'Work Sans', sans-serif",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <Heart size={15} fill={liked ? C.bg : "none"} />
              {liked ? "Remove from My List" : "Add to My List"}
            </button>
            <button
              onClick={() => onOpenDetails(featured)}
              className="ghost-btn"
              style={{
                background: "transparent",
                border: `1px solid ${C.border}`,
                color: C.text,
                padding: "11px 20px",
                fontSize: "0.875rem",
                fontFamily: "'Work Sans', sans-serif",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              See Details <ChevronRight size={15} />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
