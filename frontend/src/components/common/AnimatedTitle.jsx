import React from "react";

export default function AnimatedTitle({ text, ready }) {
  if (!text) return null;
  return (
    <span>
      {text.split("").map((ch, i) => (
        <span
          key={i}
          style={{
            display: "inline-block",
            opacity: ready ? undefined : 0,
            animation: ready ? "letterIn 0.5s ease forwards" : "none",
            animationDelay: ready ? `${i * 0.02}s` : undefined,
          }}
        >
          {ch === " " ? "\u00A0" : ch}
        </span>
      ))}
    </span>
  );
}
