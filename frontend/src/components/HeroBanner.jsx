import React from "react";
import { Star, Play, Info } from "lucide-react";

export function HeroBanner({ movie, onSelectMovie }) {
  if (!movie) return null;

  return (
    <div
      style={{
        position: "relative",
        height: "440px",
        margin: "24px 24px 32px 24px",
        borderRadius: "var(--radius-lg)",
        overflow: "hidden",
        backgroundImage: `linear-gradient(to right, rgba(10,10,15,0.95) 30%, rgba(10,10,15,0.4) 70%, transparent 100%), url(${movie.backdrop_url || movie.poster_url})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        display: "flex",
        alignItems: "center",
        padding: "0 48px",
        boxShadow: "0 20px 40px rgba(0,0,0,0.5)",
        border: "1px solid var(--border-glass)"
      }}
      className="animate-fade-in"
    >
      <div style={{ maxWidth: "560px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
          <span style={{
            background: "rgba(255,255,255,0.12)",
            padding: "4px 10px",
            borderRadius: "var(--radius-full)",
            fontSize: "0.75rem",
            fontWeight: "600",
            letterSpacing: "1px"
          }}>
            SPOTLIGHT
          </span>
          {movie.release_year && (
            <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{movie.release_year}</span>
          )}
          {movie.vote_average && (
            <span style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "0.85rem", color: "#f59e0b", fontWeight: "600" }}>
              <Star size={14} fill="#f59e0b" /> {movie.vote_average.toFixed(1)}
            </span>
          )}
        </div>

        <h1 style={{ fontSize: "2.5rem", fontWeight: "800", lineHeight: "1.1", marginBottom: "12px" }}>
          {movie.title}
        </h1>

        <p style={{
          color: "var(--text-secondary)",
          fontSize: "0.95rem",
          lineHeight: "1.5",
          marginBottom: "24px",
          display: "-webkit-box",
          WebkitLineClamp: 3,
          WebkitBoxOrient: "vertical",
          overflow: "hidden"
        }}>
          {movie.overview || "An extraordinary cinematic journey waiting to be discovered."}
        </p>

        <div style={{ display: "flex", gap: "14px" }}>
          <button
            onClick={() => onSelectMovie(movie)}
            style={{
              background: "var(--gradient-brand)",
              border: "none",
              borderRadius: "var(--radius-full)",
              padding: "12px 24px",
              color: "#fff",
              fontWeight: "600",
              fontSize: "0.9rem",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              cursor: "pointer",
              boxShadow: "var(--shadow-glow)"
            }}
          >
            <Play size={18} fill="#fff" /> Watch Info
          </button>

          <button
            onClick={() => onSelectMovie(movie)}
            style={{
              background: "rgba(255, 255, 255, 0.1)",
              border: "1px solid var(--border-glass)",
              borderRadius: "var(--radius-full)",
              padding: "12px 20px",
              color: "#fff",
              fontWeight: "500",
              fontSize: "0.9rem",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              cursor: "pointer"
            }}
          >
            <Info size={18} /> Details
          </button>
        </div>
      </div>
    </div>
  );
}
