import React, { useState, useEffect } from "react";
import { X, Star, Heart, ArrowRightLeft, Play, Tv, ExternalLink, Loader2 } from "lucide-react";
import { C } from "../../constants/theme";
import { genreColor, shade } from "../../utils/normalizers";
import Poster from "../movies/Poster";
import TrailerModal from "../movies/TrailerModal";
import { getMovieVideos, getMovieWatchProviders, recordInteraction } from "../../api/client";

export default function MovieDrawer({
  selectedMovie,
  onClose,
  liked,
  onToggleLike,
  similarList,
  loadingSimilar,
  onSelectMovie,
  onOpenCompare,
  userRating = null,
  onRateMovie,
}) {
  const [videos, setVideos] = useState([]);
  const [loadingVideos, setLoadingVideos] = useState(false);
  const [isTrailerOpen, setIsTrailerOpen] = useState(false);

  const [watchProviders, setWatchProviders] = useState(null);
  const [loadingProviders, setLoadingProviders] = useState(false);

  const [hoverRating, setHoverRating] = useState(0);

  // Fetch trailers and watch providers whenever selectedMovie changes
  useEffect(() => {
    if (!selectedMovie?.id) {
      setVideos([]);
      setWatchProviders(null);
      return;
    }

    let active = true;

    // Fetch videos
    setLoadingVideos(true);
    getMovieVideos(selectedMovie.id)
      .then((data) => {
        if (active && data?.videos) {
          setVideos(data.videos);
        }
      })
      .catch(() => {
        if (active) setVideos([]);
      })
      .finally(() => {
        if (active) setLoadingVideos(false);
      });

    // Fetch watch providers
    setLoadingProviders(true);
    getMovieWatchProviders(selectedMovie.id)
      .then((data) => {
        if (active && data) {
          setWatchProviders(data);
        }
      })
      .catch(() => {
        if (active) setWatchProviders(null);
      })
      .finally(() => {
        if (active) setLoadingProviders(false);
      });

    // Fire drawer_view interaction telemetry
    recordInteraction("drawer_view", selectedMovie.id, { title: selectedMovie.title });

    return () => {
      active = false;
    };
  }, [selectedMovie?.id]);

  const handleOpenTrailer = () => {
    setIsTrailerOpen(true);
    if (selectedMovie?.id) {
      recordInteraction("trailer_watch", selectedMovie.id, { title: selectedMovie.title });
    }
  };

  const handleStarClick = (score) => {
    if (onRateMovie && selectedMovie) {
      onRateMovie(selectedMovie.id, score);
      recordInteraction("rate", selectedMovie.id, { rating: score });
    }
  };

  return (
    <>
      <div
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 50,
          opacity: selectedMovie ? 1 : 0,
          pointerEvents: selectedMovie ? "auto" : "none",
          transition: "opacity 0.3s ease",
        }}
      >
        {/* Backdrop */}
        <div
          onClick={onClose}
          style={{
            position: "absolute",
            inset: 0,
            background: "rgba(8,5,12,0.72)",
            backdropFilter: "blur(6px)",
          }}
        />

        {/* Slide-out Panel */}
        <div
          className={selectedMovie ? "drawer-open" : ""}
          style={{
            position: "absolute",
            top: 0,
            right: 0,
            height: "100%",
            width: "100%",
            maxWidth: 440,
            background: C.surface,
            overflowY: "auto",
            transform: selectedMovie ? "translateX(0)" : "translateX(100%)",
            borderLeft: `1px solid ${C.border}`,
            boxShadow: "-24px 0 60px rgba(0,0,0,0.5)",
          }}
        >
          {selectedMovie && (
            <>
              {/* Header image / backdrop */}
              <div className="drawer-poster-in" style={{ position: "relative" }}>
                {selectedMovie.backdrop_url && !selectedMovie.backdrop_url.includes("placeholder") ? (
                  <div
                    style={{
                      position: "relative",
                      paddingTop: "56.25%",
                      overflow: "hidden",
                    }}
                  >
                    <img
                      src={selectedMovie.backdrop_url}
                      alt={selectedMovie.title}
                      style={{
                        position: "absolute",
                        inset: 0,
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                      }}
                    />
                    <div
                      style={{
                        position: "absolute",
                        inset: 0,
                        background:
                          "linear-gradient(to top, rgba(37,30,42,1) 0%, rgba(37,30,42,0.3) 60%, transparent 100%)",
                      }}
                    />
                    <div className="grain-overlay" />
                  </div>
                ) : (
                  <>
                    <Poster movie={selectedMovie} ratio="56.25%" />
                    <div
                      style={{
                        position: "absolute",
                        bottom: 0,
                        left: 0,
                        right: 0,
                        height: "50%",
                        background: "linear-gradient(to top, rgba(37,30,42,1) 0%, transparent 100%)",
                        zIndex: 10,
                      }}
                    />
                  </>
                )}

                {/* Close Button */}
                <button
                  onClick={onClose}
                  style={{
                    position: "absolute",
                    top: 14,
                    right: 14,
                    zIndex: 20,
                    background: "rgba(27,21,31,0.78)",
                    backdropFilter: "blur(8px)",
                    border: `1px solid ${C.border}`,
                    borderRadius: "50%",
                    padding: 8,
                    cursor: "pointer",
                    display: "flex",
                    color: C.text,
                    transition: "background 0.2s",
                  }}
                >
                  <X size={18} />
                </button>

                {/* Trailer Overlay Button */}
                <button
                  onClick={handleOpenTrailer}
                  disabled={loadingVideos}
                  style={{
                    position: "absolute",
                    bottom: 16,
                    right: 16,
                    zIndex: 20,
                    padding: "7px 14px",
                    background: "rgba(27, 21, 31, 0.88)",
                    backdropFilter: "blur(10px)",
                    border: `1px solid ${C.accent}`,
                    borderRadius: 20,
                    color: C.accent,
                    fontSize: "0.8rem",
                    fontWeight: 700,
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    cursor: "pointer",
                    boxShadow: "0 4px 15px rgba(0,0,0,0.5)",
                    transition: "transform 0.15s, background 0.15s",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = "scale(1.04)";
                    e.currentTarget.style.background = C.accent;
                    e.currentTarget.style.color = C.bg;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = "scale(1)";
                    e.currentTarget.style.background = "rgba(27, 21, 31, 0.88)";
                    e.currentTarget.style.color = C.accent;
                  }}
                >
                  {loadingVideos ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <Play size={14} fill="currentColor" />
                  )}
                  <span>Watch Trailer</span>
                </button>
              </div>

              {/* Content */}
              <div style={{ padding: "24px 28px" }}>
                {/* Genre tags */}
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 6,
                    marginBottom: 14,
                  }}
                >
                  {selectedMovie.genres?.map((g) => (
                    <span
                      key={g}
                      style={{
                        fontSize: "0.68rem",
                        padding: "3px 9px",
                        letterSpacing: "0.07em",
                        background: C.accentDim,
                        color: C.accent,
                        textTransform: "uppercase",
                      }}
                    >
                      {g}
                    </span>
                  ))}
                </div>

                <h2
                  className="font-display"
                  style={{
                    fontSize: "2.2rem",
                    lineHeight: 1,
                    color: C.text,
                    letterSpacing: "-0.02em",
                    marginBottom: 12,
                  }}
                >
                  {selectedMovie.title}
                </h2>

                {/* Meta */}
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    alignItems: "center",
                    gap: "8px 16px",
                    fontSize: "0.82rem",
                    color: C.muted,
                    marginBottom: 18,
                  }}
                >
                  <span>{selectedMovie.year}</span>
                  <span style={{ width: 1, height: 12, background: C.border }} />
                  <span>{selectedMovie.runtime || 110} min</span>
                  <span style={{ width: 1, height: 12, background: C.border }} />
                  <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
                    <Star size={13} fill={C.accent} color={C.accent} />
                    <span
                      style={{
                        fontWeight: 700,
                        color: C.accent,
                        fontSize: "0.9rem",
                      }}
                    >
                      {selectedMovie.rating}
                    </span>
                  </span>
                </div>

                <p
                  style={{
                    fontSize: "0.78rem",
                    color: C.muted,
                    marginBottom: 18,
                  }}
                >
                  Directed by{" "}
                  <span style={{ color: C.text, fontWeight: 600 }}>
                    {selectedMovie.director}
                  </span>
                </p>

                {/* Interactive 5-Star Rating Widget (Phase 2) */}
                <div
                  style={{
                    padding: "12px 14px",
                    background: "rgba(255, 255, 255, 0.03)",
                    border: `1px solid ${C.border}`,
                    borderRadius: 8,
                    marginBottom: 20,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <div>
                    <span
                      style={{
                        fontSize: "0.7rem",
                        textTransform: "uppercase",
                        letterSpacing: "0.08em",
                        color: C.muted,
                        display: "block",
                        marginBottom: 3,
                      }}
                    >
                      Your Rating
                    </span>
                    <span style={{ fontSize: "0.82rem", color: C.text, fontWeight: 600 }}>
                      {userRating ? `${userRating} / 5 Stars` : "Rate this film"}
                    </span>
                  </div>

                  <div style={{ display: "flex", gap: 4 }}>
                    {[1, 2, 3, 4, 5].map((star) => {
                      const isFilled = (hoverRating || userRating || 0) >= star;
                      return (
                        <button
                          key={star}
                          type="button"
                          onClick={() => handleStarClick(star)}
                          onMouseEnter={() => setHoverRating(star)}
                          onMouseLeave={() => setHoverRating(0)}
                          style={{
                            background: "transparent",
                            border: "none",
                            padding: 3,
                            cursor: "pointer",
                            transition: "transform 0.15s",
                          }}
                          title={`Rate ${star} Star${star > 1 ? "s" : ""}`}
                        >
                          <Star
                            size={18}
                            fill={isFilled ? C.accent : "none"}
                            color={isFilled ? C.accent : C.borderBright}
                            style={{
                              transform: hoverRating === star ? "scale(1.2)" : "scale(1)",
                              transition: "transform 0.15s",
                            }}
                          />
                        </button>
                      );
                    })}
                  </div>
                </div>

                <p
                  style={{
                    fontSize: "0.9rem",
                    lineHeight: 1.75,
                    color: C.muted,
                    marginBottom: 24,
                  }}
                >
                  {selectedMovie.blurb}
                </p>

                {/* Like / Favorite Button */}
                <button
                  onClick={() => onToggleLike(selectedMovie)}
                  className="cta-btn"
                  style={{
                    width: "100%",
                    padding: "13px",
                    fontSize: "0.9rem",
                    fontWeight: 700,
                    fontFamily: "'Work Sans', sans-serif",
                    cursor: "pointer",
                    marginBottom: 10,
                    border: liked ? `1px solid ${C.border}` : "none",
                    background: liked ? "transparent" : C.accent,
                    color: liked ? C.text : C.bg,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 8,
                  }}
                >
                  <Heart
                    size={15}
                    fill={liked ? C.accent : "none"}
                    color={liked ? C.accent : C.bg}
                  />
                  {liked ? "Remove from My List" : "Add to My List"}
                </button>

                {/* Compare Head-to-Head Button */}
                {onOpenCompare && (
                  <button
                    onClick={() => onOpenCompare(selectedMovie)}
                    style={{
                      width: "100%",
                      padding: "11px",
                      fontSize: "0.85rem",
                      fontWeight: 600,
                      fontFamily: "'Work Sans', sans-serif",
                      cursor: "pointer",
                      marginBottom: 26,
                      border: `1px solid ${C.borderBright}`,
                      background: "rgba(255,255,255,0.04)",
                      color: C.text,
                      borderRadius: 3,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: 8,
                      transition: "all 0.2s ease",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = C.accentDim;
                      e.currentTarget.style.borderColor = C.accent;
                      e.currentTarget.style.color = C.accent;
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                      e.currentTarget.style.borderColor = C.borderBright;
                      e.currentTarget.style.color = C.text;
                    }}
                  >
                    <ArrowRightLeft size={15} color={C.accent} />
                    Compare Head-to-Head
                  </button>
                )}

                {/* Where to Watch (Streaming Providers - Phase 3) */}
                <div style={{ marginBottom: 28 }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: 12,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <Tv size={15} color={C.teal} />
                      <h3
                        className="font-display"
                        style={{
                          fontSize: "1.15rem",
                          color: C.text,
                          margin: 0,
                          letterSpacing: "-0.01em",
                        }}
                      >
                        Where to Watch
                      </h3>
                    </div>
                    {watchProviders?.link && (
                      <a
                        href={watchProviders.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 4,
                          fontSize: "0.72rem",
                          color: C.muted,
                          textDecoration: "none",
                        }}
                      >
                        <span>TMDB Watch Guide</span>
                        <ExternalLink size={10} />
                      </a>
                    )}
                  </div>

                  {loadingProviders ? (
                    <div style={{ display: "flex", alignItems: "center", gap: 8, color: C.muted, fontSize: "0.8rem" }}>
                      <Loader2 size={14} className="animate-spin" />
                      <span>Checking streaming availability...</span>
                    </div>
                  ) : watchProviders?.flatrate && watchProviders.flatrate.length > 0 ? (
                    <div>
                      <span
                        style={{
                          fontSize: "0.7rem",
                          color: C.teal,
                          fontWeight: 600,
                          textTransform: "uppercase",
                          letterSpacing: "0.08em",
                          display: "block",
                          marginBottom: 8,
                        }}
                      >
                        Included with Subscription:
                      </span>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                        {watchProviders.flatrate.map((p) => (
                          <div
                            key={p.provider_id}
                            title={p.provider_name}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: 8,
                              padding: "4px 10px 4px 6px",
                              background: "rgba(79, 124, 116, 0.12)",
                              border: "1px solid rgba(79, 124, 116, 0.35)",
                              borderRadius: 6,
                            }}
                          >
                            {p.logo_url ? (
                              <img
                                src={p.logo_url}
                                alt={p.provider_name}
                                style={{ width: 22, height: 22, borderRadius: 4, objectFit: "cover" }}
                              />
                            ) : null}
                            <span style={{ fontSize: "0.78rem", color: C.text, fontWeight: 500 }}>
                              {p.provider_name}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : watchProviders?.rent && watchProviders.rent.length > 0 ? (
                    <div>
                      <span
                        style={{
                          fontSize: "0.7rem",
                          color: C.muted,
                          fontWeight: 600,
                          textTransform: "uppercase",
                          letterSpacing: "0.08em",
                          display: "block",
                          marginBottom: 8,
                        }}
                      >
                        Available to Rent / Buy:
                      </span>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                        {watchProviders.rent.slice(0, 4).map((p) => (
                          <div
                            key={p.provider_id}
                            title={p.provider_name}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: 8,
                              padding: "4px 10px 4px 6px",
                              background: "rgba(255, 255, 255, 0.04)",
                              border: `1px solid ${C.border}`,
                              borderRadius: 6,
                            }}
                          >
                            {p.logo_url ? (
                              <img
                                src={p.logo_url}
                                alt={p.provider_name}
                                style={{ width: 20, height: 20, borderRadius: 4, objectFit: "cover" }}
                              />
                            ) : null}
                            <span style={{ fontSize: "0.75rem", color: C.muted }}>
                              {p.provider_name}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div
                      style={{
                        padding: "10px 14px",
                        borderRadius: 6,
                        background: "rgba(255, 255, 255, 0.02)",
                        border: `1px solid ${C.border}`,
                        fontSize: "0.78rem",
                        color: C.muted,
                      }}
                    >
                      Theatrical or physical media release. Stream availability varies by region.
                    </div>
                  )}
                </div>

                {/* Similar Titles */}
                <div>
                  <h3
                    className="font-display"
                    style={{
                      fontSize: "1.2rem",
                      color: C.text,
                      marginBottom: 16,
                      letterSpacing: "-0.01em",
                    }}
                  >
                    Similar Titles
                  </h3>

                  {loadingSimilar ? (
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: 10,
                      }}
                    >
                      {[1, 2, 3].map((i) => (
                        <div
                          key={i}
                          className="shimmer"
                          style={{ height: 56, borderRadius: 2 }}
                        />
                      ))}
                    </div>
                  ) : similarList.length > 0 ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {similarList.map((m) => (
                        <button
                          key={m.id}
                          onClick={() => onSelectMovie(m)}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 12,
                            textAlign: "left",
                            background: "none",
                            border: "none",
                            cursor: "pointer",
                            padding: "8px 10px",
                            borderRadius: 2,
                            transition: "background 0.2s",
                          }}
                          onMouseEnter={(e) =>
                            (e.currentTarget.style.background = C.surfaceHigh)
                          }
                          onMouseLeave={(e) =>
                            (e.currentTarget.style.background = "none")
                          }
                        >
                          {/* Mini poster */}
                          <div
                            style={{
                              width: 36,
                              height: 52,
                              flexShrink: 0,
                              overflow: "hidden",
                              position: "relative",
                            }}
                          >
                            {m.poster_url && !m.poster_url.includes("placeholder") ? (
                              <img
                                src={m.poster_url}
                                alt={m.title}
                                style={{
                                  width: "100%",
                                  height: "100%",
                                  objectFit: "cover",
                                }}
                              />
                            ) : (
                              <div
                                style={{
                                  width: "100%",
                                  height: "100%",
                                  background: `linear-gradient(160deg, ${genreColor(
                                    m.genres[0]
                                  )} 0%, ${shade(genreColor(m.genres[0]), -25)} 100%)`,
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                }}
                              >
                                <span
                                  className="font-display"
                                  style={{
                                    fontSize: "1.1rem",
                                    color: "rgba(255,255,255,0.6)",
                                  }}
                                >
                                  {m.title.charAt(0)}
                                </span>
                              </div>
                            )}
                          </div>
                          <div style={{ flex: 1, overflow: "hidden" }}>
                            <p
                              style={{
                                fontSize: "0.875rem",
                                color: C.text,
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                              }}
                            >
                              {m.title}
                            </p>
                            <p
                              style={{
                                fontSize: "0.72rem",
                                color: C.muted,
                                marginTop: 3,
                              }}
                            >
                              {m.year} · {m.genres.slice(0, 2).join(", ")}
                            </p>
                          </div>
                          <Star size={11} fill={C.accent} color={C.accent} />
                          <span
                            style={{
                              fontSize: "0.75rem",
                              color: C.accent,
                              fontWeight: 700,
                              flexShrink: 0,
                            }}
                          >
                            {m.rating}
                          </span>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <p style={{ fontSize: "0.82rem", color: C.muted }}>
                      No similar titles found.
                    </p>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Trailer Modal Popup */}
      <TrailerModal
        isOpen={isTrailerOpen}
        onClose={() => setIsTrailerOpen(false)}
        movieTitle={selectedMovie?.title}
        videos={videos}
        loading={loadingVideos}
      />
    </>
  );
}
