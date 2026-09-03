import React from "react";
import { Star, Heart } from "lucide-react";

export function MovieCard({ movie, onSelectMovie, onToggleFavorite }) {
  const posterUrl = movie.poster_url || "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=342&q=80";

  return (
    <div
      onClick={() => onSelectMovie(movie)}
      style={{
        position: "relative",
        borderRadius: "var(--radius-md)",
        overflow: "hidden",
        background: "var(--bg-card)",
        border: "1px solid var(--border-glass)",
        cursor: "pointer",
        transition: "all 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
        display: "flex",
        flexDirection: "column"
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-6px) scale(1.02)";
        e.currentTarget.style.borderColor = "var(--border-glass-glow)";
        e.currentTarget.style.boxShadow = "0 12px 24px rgba(0,0,0,0.4)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "none";
        e.currentTarget.style.borderColor = "var(--border-glass)";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      {/* Rating Badge */}
      <div style={{
        position: "absolute",
        top: "10px",
        left: "10px",
        background: "rgba(10, 10, 15, 0.8)",
        backdropFilter: "blur(8px)",
        padding: "4px 8px",
        borderRadius: "var(--radius-sm)",
        display: "flex",
        alignItems: "center",
        gap: "4px",
        fontSize: "0.75rem",
        fontWeight: "700",
        color: "#f59e0b",
        zIndex: 2
      }}>
        <Star size={12} fill="#f59e0b" />
        {movie.vote_average ? movie.vote_average.toFixed(1) : "N/A"}
      </div>

      {/* Favorite Button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onToggleFavorite && onToggleFavorite(movie);
        }}
        style={{
          position: "absolute",
          top: "10px",
          right: "10px",
          background: "rgba(10, 10, 15, 0.8)",
          backdropFilter: "blur(8px)",
          border: "none",
          borderRadius: "50%",
          width: "30px",
          height: "30px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          zIndex: 2
        }}
      >
        <Heart size={14} color={movie.is_favorite ? "#ec4899" : "#fff"} fill={movie.is_favorite ? "#ec4899" : "none"} />
      </button>

      {/* Poster Image */}
      <div style={{ width: "100%", paddingTop: "145%", position: "relative", background: "#181824" }}>
        <img
          src={posterUrl}
          alt={movie.title}
          loading="lazy"
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover"
          }}
        />
      </div>

      {/* Info Container */}
      <div style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "6px", flex: 1 }}>
        <h4 style={{
          fontSize: "0.9rem",
          fontWeight: "600",
          color: "#fff",
          lineHeight: "1.2",
          display: "-webkit-box",
          WebkitLineClamp: 1,
          WebkitBoxOrient: "vertical",
          overflow: "hidden"
        }}>
          {movie.title}
        </h4>

        {movie.reason && (
          <span style={{
            fontSize: "0.72rem",
            color: "var(--accent-secondary)",
            background: "rgba(168, 85, 247, 0.12)",
            padding: "2px 6px",
            borderRadius: "4px",
            display: "-webkit-box",
            WebkitLineClamp: 1,
            WebkitBoxOrient: "vertical",
            overflow: "hidden"
          }}>
            {movie.reason}
          </span>
        )}

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "auto" }}>
          <span>{movie.release_year || "Film"}</span>
          <span>{movie.genres?.[0] || ""}</span>
        </div>
      </div>
    </div>
  );
}
