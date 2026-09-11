import React, { useState } from "react";
import { Heart } from "lucide-react";
import { C } from "../../constants/theme";
import Poster from "./Poster";
import RatingRing from "../common/RatingRing";

export default function MovieCard({
  movie,
  liked,
  onToggleLike,
  onOpen,
  compact,
  delay = 0,
}) {
  const [wasLiked, setWasLiked] = useState(false);
  const [tilt, setTilt] = useState({ rx: 0, ry: 0, gx: 50, gy: 50 });

  const handleLike = (e) => {
    e.stopPropagation();
    if (!liked) setWasLiked(true);
    onToggleLike(movie);
    setTimeout(() => setWasLiked(false), 500);
  };

  const handleMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width;
    const py = (e.clientY - rect.top) / rect.height;
    setTilt({
      rx: (0.5 - py) * 12,
      ry: (px - 0.5) * 12,
      gx: px * 100,
      gy: py * 100,
    });
  };

  const resetTilt = () => setTilt({ rx: 0, ry: 0, gx: 50, gy: 50 });

  return (
    <div
      className="movie-card grid-card"
      style={{
        flexShrink: compact ? 0 : undefined,
        width: compact ? "clamp(140px, 20vw, 172px)" : undefined,
        animationDelay: `${delay}ms`,
      }}
    >
      <div
        className="tilt-card"
        onClick={() => onOpen(movie)}
        onMouseMove={handleMove}
        onMouseLeave={resetTilt}
      >
        <div className="perf-strip" style={{ background: C.bg }} />
        <div
          style={{
            transition: "transform 0.15s ease",
            transform: `rotateX(${tilt.rx}deg) rotateY(${tilt.ry}deg)`,
          }}
        >
          <Poster movie={movie} ratio="150%">
            {/* Cursor-following radial highlight */}
            <div
              style={{
                position: "absolute",
                inset: 0,
                pointerEvents: "none",
                zIndex: 3,
                background: `radial-gradient(circle at ${tilt.gx}% ${tilt.gy}%, rgba(255,255,255,0.16), transparent 55%)`,
              }}
            />

            {/* Heart / Favorite Toggle */}
            <button
              onClick={handleLike}
              className={`heart-btn${liked || wasLiked ? " liked" : ""}`}
              aria-label={
                liked
                  ? `Remove ${movie.title} from My List`
                  : `Add ${movie.title} to My List`
              }
              style={{
                position: "absolute",
                top: 8,
                left: 8,
                zIndex: 4,
                background: "rgba(27,21,31,0.72)",
                backdropFilter: "blur(6px)",
                border: "none",
                borderRadius: "50%",
                padding: "7px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Heart
                size={14}
                fill={liked ? C.accent : "none"}
                color={liked ? C.accent : C.text}
                style={{ transition: "fill 0.2s ease, color 0.2s ease" }}
              />
            </button>

            {/* Radial Rating Ring */}
            <div
              style={{
                position: "absolute",
                top: 6,
                right: 6,
                zIndex: 4,
                background: "rgba(27,21,31,0.55)",
                borderRadius: "9999px",
                padding: 2,
              }}
            >
              <RatingRing rating={movie.rating} size={34} />
            </div>

            {/* Genre ribbon */}
            <div
              style={{
                position: "absolute",
                bottom: 0,
                left: 0,
                right: 0,
                zIndex: 4,
                background:
                  "linear-gradient(to top, rgba(27,21,31,0.92) 0%, transparent 100%)",
                padding: "20px 8px 6px",
              }}
            >
              <span
                style={{
                  fontSize: "0.65rem",
                  color: C.muted,
                  letterSpacing: "0.04em",
                }}
              >
                {movie.genres?.slice(0, 2).join(" · ")}
              </span>
            </div>
          </Poster>
        </div>
        <div className="perf-strip" style={{ background: C.bg }} />
      </div>

      <div style={{ paddingTop: "10px", paddingLeft: 2, paddingRight: 2 }}>
        <h4
          className="font-display"
          style={{
            fontSize: "1.05rem",
            lineHeight: 1.25,
            color: C.text,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            letterSpacing: "-0.01em",
          }}
          title={movie.title}
        >
          {movie.title}
        </h4>
        <p style={{ fontSize: "0.72rem", color: C.muted, marginTop: 3 }}>
          {movie.year} · {movie.director?.split(" ").slice(-1)[0]}
        </p>
        <p
          style={{
            fontSize: "0.72rem",
            color: C.muted,
            marginTop: 6,
            lineHeight: 1.5,
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {movie.blurb}
        </p>
      </div>
    </div>
  );
}
