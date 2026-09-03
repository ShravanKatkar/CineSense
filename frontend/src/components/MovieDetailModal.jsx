import React, { useState, useEffect } from "react";
import { X, Star, Clock, Calendar, Film, Heart } from "lucide-react";
import { getMovieDetail, getSimilarMovies, upsertRating } from "../api/client";
import { MovieCard } from "./MovieCard";

export function MovieDetailModal({ movie, onClose, onSelectMovie }) {
  const [detail, setDetail] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [userRating, setUserRating] = useState(0);

  useEffect(() => {
    if (movie) {
      getMovieDetail(movie.id).then(setDetail).catch(console.error);
      getSimilarMovies(movie.id, 6).then(setSimilar).catch(console.error);
    }
  }, [movie]);

  if (!movie) return null;

  const handleRate = async (rating) => {
    setUserRating(rating);
    try {
      await upsertRating(movie.id, rating);
    } catch (err) {
      console.error("Rating submission failed", err);
    }
  };

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: "rgba(10, 10, 15, 0.88)",
      backdropFilter: "blur(14px)",
      zIndex: 220,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "24px"
    }}>
      <div className="glass-panel animate-fade-in" style={{
        width: "100%",
        maxWidth: "920px",
        maxHeight: "90vh",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        position: "relative"
      }}>
        <button
          onClick={onClose}
          style={{
            position: "absolute",
            top: "16px",
            right: "16px",
            background: "rgba(10, 10, 15, 0.7)",
            border: "1px solid var(--border-glass)",
            borderRadius: "50%",
            width: "36px",
            height: "36px",
            color: "#fff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            zIndex: 10
          }}
        >
          <X size={20} />
        </button>

        <div style={{ overflowY: "auto", flex: 1 }}>
          {/* Backdrop Header */}
          <div style={{
            height: "300px",
            backgroundImage: `linear-gradient(to top, var(--bg-primary) 0%, transparent 100%), url(${detail?.backdrop_url || movie.backdrop_url || movie.poster_url})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            padding: "32px",
            display: "flex",
            alignItems: "flex-end"
          }}>
            <div>
              <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "8px" }}>
                {movie.release_year && (
                  <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{movie.release_year}</span>
                )}
                {movie.certification && (
                  <span style={{ border: "1px solid var(--border-glass)", padding: "2px 6px", borderRadius: "4px", fontSize: "0.75rem" }}>
                    {movie.certification}
                  </span>
                )}
                {detail?.runtime && (
                  <span style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                    <Clock size={14} /> {detail.runtime} mins
                  </span>
                )}
              </div>
              <h2 style={{ fontSize: "2.2rem", fontWeight: "800" }}>{movie.title}</h2>
            </div>
          </div>

          {/* Details Body */}
          <div style={{ padding: "32px", display: "flex", flexDirection: "column", gap: "24px" }}>
            <p style={{ fontSize: "1rem", color: "var(--text-secondary)", lineHeight: "1.6" }}>
              {detail?.overview || movie.overview || "Overview coming soon."}
            </p>

            {/* Rate This Movie */}
            <div style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid var(--border-glass)",
              borderRadius: "var(--radius-md)",
              padding: "16px 24px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between"
            }}>
              <span style={{ fontWeight: "600", fontSize: "0.95rem" }}>Rate this movie:</span>
              <div style={{ display: "flex", gap: "6px" }}>
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => handleRate(star)}
                    style={{ background: "transparent", border: "none", cursor: "pointer" }}
                  >
                    <Star
                      size={22}
                      color={userRating >= star ? "#f59e0b" : "var(--text-muted)"}
                      fill={userRating >= star ? "#f59e0b" : "none"}
                    />
                  </button>
                ))}
              </div>
            </div>

            {/* Similar Movies */}
            {similar.length > 0 && (
              <div>
                <h3 style={{ fontSize: "1.2rem", fontWeight: "700", marginBottom: "16px" }}>Similar Recommendations</h3>
                <div style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
                  gap: "14px"
                }}>
                  {similar.map((sim) => (
                    <MovieCard key={sim.id} movie={sim} onSelectMovie={onSelectMovie} />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
