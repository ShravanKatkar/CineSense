import React from "react";
import { Sparkles } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { C } from "../../constants/theme";
import { shade } from "../../utils/normalizers";

export default function TasteProfile({ likedCount, tasteData }) {
  if (likedCount === 0 || !tasteData || tasteData.length === 0) return null;

  return (
    <section
      className="slide-up"
      style={{
        maxWidth: "80rem",
        margin: "0 auto",
        padding: "1.5rem 1.5rem",
      }}
    >
      <div
        style={{
          background: C.surface,
          border: `1px solid ${C.border}`,
          padding: "24px 28px",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Decorative corner */}
        <div
          style={{
            position: "absolute",
            top: -20,
            right: -20,
            width: 100,
            height: 100,
            background: `radial-gradient(circle, ${C.accentDim} 0%, transparent 70%)`,
            pointerEvents: "none",
          }}
        />
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
          <Sparkles size={16} color={C.accent} />
          <h2 className="font-display" style={{ fontSize: "1.5rem", color: C.text }}>
            Your Taste Profile
          </h2>
        </div>
        <p style={{ fontSize: "0.78rem", color: C.muted, marginBottom: 20 }}>
          Built from {likedCount} title{likedCount !== 1 ? "s" : ""} in your list.
        </p>
        <ResponsiveContainer width="100%" height={tasteData.length * 30 + 20}>
          <BarChart
            data={tasteData}
            layout="vertical"
            margin={{ left: 0, right: 24, top: 0, bottom: 0 }}
          >
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="genre"
              width={88}
              tick={{ fill: C.muted, fontSize: 12, fontFamily: "'Work Sans'" }}
              axisLine={false}
              tickLine={false}
            />
            <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={13} isAnimationActive>
              {tasteData.map((_, i) => (
                <Cell
                  key={i}
                  fill={
                    i === 0
                      ? C.accent
                      : i % 2 === 0
                      ? C.teal
                      : shade(C.teal, -15)
                  }
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
