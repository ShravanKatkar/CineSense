import React, { useState } from "react";
import { Film, Sparkles, Search, User, SlidersHorizontal } from "lucide-react";

export function Navbar({ onOpenAI, onOpenOnboarding, onSearchSubmit }) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearchSubmit(query.trim());
    }
  };

  return (
    <nav className="glass-panel" style={{
      position: "sticky",
      top: "16px",
      margin: "0 24px",
      zIndex: 100,
      padding: "12px 24px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "16px"
    }}>
      {/* Brand */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px", cursor: "pointer" }} onClick={() => window.location.reload()}>
        <div style={{
          width: "38px",
          height: "38px",
          borderRadius: "10px",
          background: "var(--gradient-brand)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "var(--shadow-glow)"
        }}>
          <Film size={22} color="#fff" />
        </div>
        <span style={{ fontSize: "1.4rem", fontWeight: "800", letterSpacing: "-0.5px" }} className="gradient-text">
          CineSense
        </span>
      </div>

      {/* Search Input */}
      <form onSubmit={handleSubmit} style={{ flex: 1, maxWidth: "480px", position: "relative" }}>
        <input
          type="text"
          placeholder="Search movies by title, actor, or genre..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{
            width: "100%",
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid var(--border-glass)",
            borderRadius: "var(--radius-full)",
            padding: "10px 16px 10px 42px",
            color: "#fff",
            fontSize: "0.9rem",
            outline: "none",
            transition: "all 0.2s"
          }}
        />
        <Search size={18} color="var(--text-muted)" style={{ position: "absolute", left: "14px", top: "50%", transform: "translateY(-50%)" }} />
      </form>

      {/* Actions */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <button
          onClick={onOpenAI}
          className="pulse-glow"
          style={{
            background: "var(--gradient-brand)",
            border: "none",
            borderRadius: "var(--radius-full)",
            padding: "8px 18px",
            color: "#fff",
            fontWeight: "600",
            fontSize: "0.85rem",
            display: "flex",
            alignItems: "center",
            gap: "6px",
            cursor: "pointer"
          }}
        >
          <Sparkles size={16} />
          AI Assistant
        </button>

        <button
          onClick={onOpenOnboarding}
          style={{
            background: "rgba(255, 255, 255, 0.08)",
            border: "1px solid var(--border-glass)",
            borderRadius: "var(--radius-full)",
            padding: "8px 14px",
            color: "#fff",
            fontWeight: "500",
            fontSize: "0.85rem",
            display: "flex",
            alignItems: "center",
            gap: "6px",
            cursor: "pointer"
          }}
        >
          <SlidersHorizontal size={16} />
          Onboarding
        </button>
      </div>
    </nav>
  );
}
