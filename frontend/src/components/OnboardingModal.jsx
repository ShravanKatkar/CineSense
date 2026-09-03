import React, { useState, useEffect } from "react";
import { X, Check, Star, RefreshCw } from "lucide-react";
import { getColdStartMovies, upsertRating } from "../api/client";

export function OnboardingModal({ isOpen, onClose, onComplete }) {
  const [movies, setMovies] = useState([]);
  const [ratings, setRatings] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      getColdStartMovies(16)
        .then(setMovies)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleRate = async (movieId, rating) => {
    setRatings((prev) => ({ ...prev, [movieId]: rating }));
    try {
      await upsertRating(movieId, rating);
    } catch (err) {
      console.error("Failed to submit rating", err);
    }
  };

  const ratedCount = Object.keys(ratings).length;

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: "rgba(10, 10, 15, 0.88)",
      backdropFilter: "blur(12px)",
      zIndex: 210,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "24px"
    }}>
      <div className="glass-panel animate-fade-in" style={{
        width: "100%",
        maxWidth: "900px",
        maxHeight: "85vh",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden"
      }}>
        {/* Header */}
        <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--border-glass)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h3 style={{ fontSize: "1.2rem", fontWeight: "700" }}>Taste Onboarding</h3>
            <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>Rate 5 or more movies to unlock your personalized recommendation feed.</p>
          </div>
          <button onClick={onClose} style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}>
            <X size={22} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: "24px", overflowY: "auto", flex: 1 }}>
          {loading ? (
            <div style={{ textAlign: "center", padding: "40px 0" }}>Loading onboarding selection...</div>
          ) : (
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
              gap: "18px"
            }}>
              {movies.map((m) => (
                <div key={m.id} style={{
                  background: "var(--bg-card)",
                  border: ratings[m.id] ? "1px solid var(--accent-primary)" : "1px solid var(--border-glass)",
                  borderRadius: "var(--radius-md)",
                  padding: "12px",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "10px"
                }}>
                  <img
                    src={m.poster_url}
                    alt={m.title}
                    style={{ width: "100%", height: "180px", objectFit: "cover", borderRadius: "var(--radius-sm)" }}
                  />
                  <h4 style={{ fontSize: "0.85rem", textAlign: "center", fontWeight: "600", color: "#fff" }}>{m.title}</h4>

                  {/* 5-Star Rating Buttons */}
                  <div style={{ display: "flex", gap: "4px" }}>
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        onClick={() => handleRate(m.id, star)}
                        style={{
                          background: "transparent",
                          border: "none",
                          cursor: "pointer"
                        }}
                      >
                        <Star
                          size={16}
                          color={ratings[m.id] >= star ? "#f59e0b" : "var(--text-muted)"}
                          fill={ratings[m.id] >= star ? "#f59e0b" : "none"}
                        />
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: "16px 24px", borderTop: "1px solid var(--border-glass)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
            Rated: <strong>{ratedCount} / 5 required</strong>
          </span>
          <button
            onClick={() => {
              onClose();
              onComplete && onComplete();
            }}
            disabled={ratedCount < 3}
            style={{
              background: ratedCount >= 3 ? "var(--gradient-brand)" : "rgba(255,255,255,0.1)",
              border: "none",
              borderRadius: "var(--radius-full)",
              padding: "10px 24px",
              color: "#fff",
              fontWeight: "600",
              cursor: ratedCount >= 3 ? "pointer" : "not-allowed"
            }}
          >
            Finished Onboarding
          </button>
        </div>
      </div>
    </div>
  );
}
