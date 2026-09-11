import React from "react";
import { Star } from "lucide-react";
import { C } from "../../constants/theme";

export default function Ticker({ movies }) {
  if (!movies || movies.length === 0) return null;

  const items = [...movies, ...movies].map((m, i) => (
    <span
      key={i}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        marginRight: 36,
        color: C.muted,
        fontSize: "0.75rem",
        letterSpacing: "0.05em",
      }}
    >
      <Star size={10} fill={C.accent} color={C.accent} />
      <span
        style={{
          color: C.text,
          fontFamily: "'Big Shoulders Display', sans-serif",
          fontSize: "0.9rem",
        }}
      >
        {m.title}
      </span>
      <span>{m.rating}</span>
    </span>
  ));

  return (
    <div
      className="ticker-wrap"
      style={{
        padding: "10px 0",
        borderTop: `1px solid ${C.border}`,
        borderBottom: `1px solid ${C.border}`,
        background: C.surface,
      }}
    >
      <div className="ticker-inner">{items}</div>
    </div>
  );
}
