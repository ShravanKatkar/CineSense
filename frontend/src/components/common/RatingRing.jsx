import React, { useState, useEffect, useRef } from "react";
import { C } from "../../constants/theme";

export default function RatingRing({ rating, size = 34 }) {
  const [filled, setFilled] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setFilled(true);
            obs.disconnect();
          }
        });
      },
      { threshold: 0.4 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  const r = (size - 4) / 2;
  const c = 2 * Math.PI * r;
  const pct = rating / 10;

  return (
    <div
      ref={ref}
      style={{
        position: "relative",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        width: size,
        height: size,
      }}
    >
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgba(255,255,255,0.18)"
          strokeWidth="2.5"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={C.accent}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={filled ? c * (1 - pct) : c}
          style={{ transition: "stroke-dashoffset 1s ease" }}
        />
      </svg>
      <span
        className="font-display"
        style={{ position: "absolute", fontSize: size * 0.34, color: C.text }}
      >
        {rating}
      </span>
    </div>
  );
}
