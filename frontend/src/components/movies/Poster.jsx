import React, { useState } from "react";
import { C } from "../../constants/theme";
import { genreColor, shade } from "../../utils/normalizers";

export default function Poster({ movie, ratio, children, scanline, animated }) {
  const [loaded, setLoaded] = useState(false);
  const [err, setErr] = useState(false);
  const color = genreColor(movie?.genres?.[0] || "Cinema");
  const hasImg = movie?.poster_url && !err && !movie.poster_url.includes("placeholder");

  return (
    <div
      className={`card-poster${scanline ? " scanline-poster" : ""}`}
      style={{
        position: "relative",
        width: "100%",
        paddingTop: ratio,
        backgroundColor: C.surface,
        overflow: "hidden",
      }}
    >
      {/* Gradient initial monogram */}
      <div
        className={animated ? "ken-burns" : ""}
        style={{
          position: "absolute",
          inset: 0,
          background: `linear-gradient(160deg, ${color} 0%, ${shade(color, -30)} 100%)`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span
          className="font-display"
          style={{
            fontSize: "5rem",
            color: "rgba(255,255,255,0.13)",
            userSelect: "none",
            letterSpacing: "-3px",
          }}
        >
          {(movie?.title || "M").charAt(0)}
        </span>
      </div>

      {/* Real poster */}
      {hasImg && (
        <img
          src={movie.poster_url}
          alt={movie.title}
          loading="lazy"
          className="poster-img"
          onLoad={() => setLoaded(true)}
          onError={() => setErr(true)}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
            opacity: loaded ? 1 : 0,
          }}
        />
      )}

      {/* Shine */}
      <div className="card-shine" />

      {/* Film grain */}
      <div className="grain-overlay" />

      {children}
    </div>
  );
}
