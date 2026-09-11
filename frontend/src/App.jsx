import React, { useState, useEffect, useMemo, useCallback, useRef } from "react";
import {
  Search,
  Star,
  Heart,
  X,
  Sparkles,
  Film,
  Loader2,
  ArrowRight,
  ChevronRight,
  Clapperboard,
  Zap,
  ArrowRightLeft,
  Compass,
  Users,
  Award,
  User as UserIcon,
  LogOut,
  Radio,
} from "lucide-react";

import { C, STYLES } from "./constants/theme";
import { FALLBACK } from "./constants/fallbackCatalog";
import { normalizeMovie } from "./utils/normalizers";

import Ticker from "./components/common/Ticker";
import Reveal from "./components/common/Reveal";
import BillboardHero from "./components/hero/BillboardHero";
import MovieCard from "./components/movies/MovieCard";
import GenreChip from "./components/movies/GenreChip";
import TasteProfile from "./components/profile/TasteProfile";
import MovieDrawer from "./components/drawer/MovieDrawer";
import ChatModal from "./components/assistant/ChatModal";
import MovieComparisonModal from "./components/features/MovieComparisonModal";
import WatchTonightModal from "./components/features/WatchTonightModal";
import MovieNightModal from "./components/features/MovieNightModal";
import EvaluationDashboardModal from "./components/evaluation/EvaluationDashboardModal";
import AuthModal from "./components/auth/AuthModal";

import {
  getPopularMovies,
  getTrendingMovies,
  getForYouFeed,
  searchMovies,
  getSimilarMovies,
  listGenres,
  performRagSearch,
  loginUser,
  registerUser,
  logoutUser,
  getCurrentUser,
  getMyRatings,
  upsertRating,
  getFavorites,
  addFavorite,
  removeFavorite,
  getUpcomingMovies,
  getSessionTunedRecs,
  recordInteraction,
} from "./api/client";

export default function MatineeApp() {
  const [moviesList, setMoviesList] = useState(() => FALLBACK.map(normalizeMovie));
  const [activeTab, setActiveTab] = useState("discover");
  const [query, setQuery] = useState("");
  const [sortBy, setSortBy] = useState("rating");
  const [minRating, setMinRating] = useState(0);
  const [activeGenres, setActiveGenres] = useState(new Set());
  const [genreOptions, setGenreOptions] = useState([]);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [similarList, setSimilarList] = useState([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const [backendFeed, setBackendFeed] = useState(null);
  const [isAiMode, setIsAiMode] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [userRatings, setUserRatings] = useState({});
  const [upcomingMovies, setUpcomingMovies] = useState([]);
  const [sessionSeeds, setSessionSeeds] = useState([]);
  const [sessionTunedRecs, setSessionTunedRecs] = useState([]);
  const [isCompareOpen, setIsCompareOpen] = useState(false);
  const [compareMovieA, setCompareMovieA] = useState(null);
  const [compareMovieB, setCompareMovieB] = useState(null);
  const [isWatchTonightOpen, setIsWatchTonightOpen] = useState(false);
  const [isMovieNightOpen, setIsMovieNightOpen] = useState(false);
  const [isEvalOpen, setIsEvalOpen] = useState(false);
  const [aiQuery, setAiQuery] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState(null);
  const [connected, setConnected] = useState(false);
  const [gridKey, setGridKey] = useState(0);
  const [showIntro, setShowIntro] = useState(() => {
    if (
      typeof window !== "undefined" &&
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    )
      return false;
    return true;
  });

  const spotlightRef = useRef(null);
  const heroReady = !showIntro;

  const [likedIds, setLikedIds] = useState(() => {
    try {
      return new Set(JSON.parse(localStorage.getItem("mtl_liked") || "[]"));
    } catch {
      return new Set([27, 1]);
    }
  });

  const [likedMap, setLikedMap] = useState(() => {
    try {
      return new Map(JSON.parse(localStorage.getItem("mtl_liked_map") || "[]"));
    } catch {
      return new Map();
    }
  });

  /* Persist liked state */
  useEffect(() => {
    try {
      localStorage.setItem("mtl_liked", JSON.stringify([...likedIds]));
      localStorage.setItem(
        "mtl_liked_map",
        JSON.stringify([...likedMap.entries()])
      );
    } catch {}
  }, [likedIds, likedMap]);

  /* Intro countdown timer */
  useEffect(() => {
    if (!showIntro) return;
    const t = setTimeout(() => setShowIntro(false), 2300);
    return () => clearTimeout(t);
  }, [showIntro]);

  /* Spotlight cursor tracking */
  useEffect(() => {
    const el = spotlightRef.current;
    if (!el) return;
    const handleMove = (e) => {
      el.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
    };
    window.addEventListener("mousemove", handleMove, { passive: true });
    return () => window.removeEventListener("mousemove", handleMove);
  }, []);

  /* Initial data load and user session restoration */
  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      try {
        const [popRes, genresRes, upRes, userRes] = await Promise.allSettled([
          getPopularMovies(36),
          listGenres(),
          getUpcomingMovies(1),
          getCurrentUser(),
        ]);

        if (cancelled) return;

        if (popRes.status === "fulfilled") {
          const raw = popRes.value;
          const items = Array.isArray(raw) ? raw : (raw?.items || []);
          if (items.length > 0) {
            const norm = items.map(normalizeMovie).filter(Boolean);
            if (norm.length > 0) {
              setMoviesList(norm);
              setConnected(true);
            }
          }
        }

        if (genresRes.status === "fulfilled" && Array.isArray(genresRes.value)) {
          setGenreOptions(genresRes.value);
        }

        if (upRes.status === "fulfilled") {
          const upItems = Array.isArray(upRes.value) ? upRes.value : (upRes.value?.items || []);
          if (upItems.length > 0) {
            setUpcomingMovies(upItems.map(normalizeMovie).filter(Boolean));
          }
        }

        if (userRes.status === "fulfilled" && userRes.value) {
          const user = userRes.value;
          setCurrentUser(user);
          // Sync ratings & favorites from cloud
          getMyRatings().then((ratings) => {
            if (Array.isArray(ratings)) {
              const rMap = {};
              ratings.forEach((r) => {
                if (r.movie_id) rMap[r.movie_id] = r.rating;
              });
              setUserRatings(rMap);
            }
          }).catch(() => {});

          getFavorites().then((favs) => {
            if (Array.isArray(favs) && favs.length > 0) {
              setLikedIds(new Set(favs.map((f) => f.id)));
              setLikedMap(new Map(favs.map((f) => [f.id, normalizeMovie(f)])));
            }
          }).catch(() => {});
        }

        try {
          const feedRes = await getForYouFeed();
          if (!cancelled && feedRes?.rows?.length > 0) {
            setBackendFeed(feedRes);
            setConnected(true);
            const feedItems = feedRes.rows.flatMap((r) => r.items || []).map(normalizeMovie).filter(Boolean);
            if (feedItems.length > 0) {
              setMoviesList((prev) => {
                const existingIds = new Set(feedItems.map((m) => m.id));
                return [...feedItems, ...prev.filter((m) => !existingIds.has(m.id))];
              });
            }
          }
        } catch {}
      } catch {
        // Keep offline fallback catalog
      }
    }

    loadData();
    return () => {
      cancelled = true;
    };
  }, []);

  /* Session Tuning Effect (Phase 4) */
  useEffect(() => {
    if (sessionSeeds.length === 0) return;
    let active = true;
    getSessionTunedRecs(sessionSeeds)
      .then((recs) => {
        if (active && Array.isArray(recs) && recs.length > 0) {
          setSessionTunedRecs(recs.map(normalizeMovie).filter(Boolean));
        }
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [sessionSeeds]);

  /* Load similar movies when detail drawer opens */
  useEffect(() => {
    if (!selectedMovie) {
      setSimilarList([]);
      return;
    }

    let cancelled = false;
    setLoadingSimilar(true);

    async function fetchSimilar() {
      try {
        const res = await getSimilarMovies(selectedMovie.id, 6);
        if (cancelled) return;
        const items = (res?.items || res || [])
          .map(normalizeMovie)
          .filter(Boolean)
          .filter((m) => m.id !== selectedMovie.id);
        setSimilarList(items.slice(0, 5));
      } catch {
        if (cancelled) return;
        const pool = moviesList.filter((m) => m.id !== selectedMovie.id);
        const shared = pool.filter((m) =>
          m.genres.some((g) => selectedMovie.genres.includes(g))
        );
        setSimilarList((shared.length >= 3 ? shared : pool).slice(0, 5));
      } finally {
        if (!cancelled) setLoadingSimilar(false);
      }
    }

    fetchSimilar();
    return () => {
      cancelled = true;
    };
  }, [selectedMovie, moviesList]);

  /* Auth Success Callback (Phase 2) */
  const handleAuthSuccess = async (user) => {
    setCurrentUser(user);
    setIsAuthOpen(false);

    // Merge any existing local guest likes into user's cloud account
    if (likedIds.size > 0) {
      for (const id of likedIds) {
        addFavorite(id).catch(() => {});
      }
    }

    // Refresh cloud favorites, ratings, and personalized feed
    try {
      const [favs, ratings, feedRes] = await Promise.all([
        getFavorites().catch(() => []),
        getMyRatings().catch(() => []),
        getForYouFeed().catch(() => null),
      ]);

      if (Array.isArray(favs) && favs.length > 0) {
        setLikedIds(new Set(favs.map((f) => f.id)));
        setLikedMap(new Map(favs.map((f) => [f.id, normalizeMovie(f)])));
      }
      if (Array.isArray(ratings)) {
        const rMap = {};
        ratings.forEach((r) => {
          if (r.movie_id) rMap[r.movie_id] = r.rating;
        });
        setUserRatings(rMap);
      }
      if (feedRes?.rows?.length > 0) {
        setBackendFeed(feedRes);
      }
    } catch {}
  };

  /* Sign Out Handler */
  const handleSignOut = async () => {
    await logoutUser();
    setCurrentUser(null);
    setUserRatings({});
    // Re-fetch anonymous feed
    getForYouFeed().then((feedRes) => {
      if (feedRes?.rows) setBackendFeed(feedRes);
    }).catch(() => {});
  };

  /* Rate Movie Handler (Phase 2) */
  const handleRateMovie = async (movieId, score) => {
    setUserRatings((prev) => ({ ...prev, [movieId]: score }));
    if (currentUser) {
      try {
        await upsertRating(movieId, score);
      } catch (err) {
        console.warn("Error updating cloud rating:", err);
      }
    } else {
      setAuthMode("login");
      setIsAuthOpen(true);
    }
  };

  /* Open Movie with telemetry and session seed tracking (Phase 4) */
  const handleOpenMovie = useCallback((movie) => {
    if (!movie) return;
    setSelectedMovie(movie);
    recordInteraction("click", movie.id, { title: movie.title });
    setSessionSeeds((prev) => {
      const filtered = prev.filter((id) => id !== movie.id);
      return [movie.id, ...filtered].slice(0, 5);
    });
  }, []);

  /* Like / Favorite handler with cloud sync (Phase 2) */
  const toggleLike = useCallback((movie) => {
    if (!movie) return;
    const isCurrentlyLiked = likedIds.has(movie.id);

    setLikedIds((prev) => {
      const next = new Set(prev);
      if (next.has(movie.id)) {
        next.delete(movie.id);
      } else {
        next.add(movie.id);
      }
      return next;
    });

    setLikedMap((prev) => {
      const next = new Map(prev);
      if (next.has(movie.id)) {
        next.delete(movie.id);
      } else {
        next.set(movie.id, movie);
      }
      return next;
    });

    if (currentUser) {
      if (isCurrentlyLiked) {
        removeFavorite(movie.id).catch(() => {});
      } else {
        addFavorite(movie.id).catch(() => {});
      }
    }

    recordInteraction(isCurrentlyLiked ? "unfavorite" : "favorite", movie.id, { title: movie.title });
  }, [likedIds, currentUser]);

  /* AI RAG search handler */
  const handleAiSearch = async (e) => {
    e?.preventDefault();
    if (!aiQuery.trim() || aiLoading) return;
    setAiLoading(true);
    setAiResponse(null);

    try {
      const res = await performRagSearch(aiQuery.trim(), 8);
      setAiResponse(res);
      if (res?.items?.length > 0) {
        const norm = res.items.map(normalizeMovie).filter(Boolean);
        setMoviesList((prev) => {
          const existingIds = new Set(prev.map((m) => m.id));
          const newItems = norm.filter((m) => !existingIds.has(m.id));
          return [...newItems, ...prev];
        });
      }
    } catch (err) {
      setAiResponse({
        intro: "Unable to complete AI search. Please check your connection.",
        items: [],
      });
    } finally {
      setAiLoading(false);
    }
  };

  /* Filtered and sorted browse list */
  const filteredBrowse = useMemo(() => {
    let list = moviesList;

    if (query.trim()) {
      const q = query.toLowerCase();
      list = list.filter(
        (m) =>
          m.title.toLowerCase().includes(q) ||
          m.director.toLowerCase().includes(q) ||
          m.genres.some((g) => g.toLowerCase().includes(q))
      );
    }

    if (minRating > 0) {
      list = list.filter((m) => m.rating >= minRating);
    }

    if (activeGenres.size > 0) {
      list = list.filter((m) => m.genres.some((g) => activeGenres.has(g)));
    }

    return [...list].sort((a, b) => {
      if (sortBy === "rating") return b.rating - a.rating;
      if (sortBy === "year") return b.year - a.year;
      if (sortBy === "title") return a.title.localeCompare(b.title);
      return 0;
    });
  }, [moviesList, query, minRating, activeGenres, sortBy]);

  /* Genre list for filter bar */
  const availableGenres = useMemo(() => {
    if (genreOptions.length > 0) {
      return genreOptions.map((g) => (typeof g === "string" ? g : g.name));
    }
    const set = new Set();
    moviesList.forEach((m) => m.genres?.forEach((g) => set.add(g)));
    return [...set].sort();
  }, [genreOptions, moviesList]);

  /* Taste profile calculation from liked movies */
  const likedMovies = useMemo(() => {
    const fromMap = [...likedMap.values()];
    if (fromMap.length > 0) return fromMap;
    return moviesList.filter((m) => likedIds.has(m.id));
  }, [likedMap, likedIds, moviesList]);

  const tasteData = useMemo(() => {
    const counts = {};
    likedMovies.forEach((m) => {
      m.genres?.forEach((g) => {
        counts[g] = (counts[g] || 0) + 1;
      });
    });
    return Object.entries(counts)
      .map(([genre, count]) => ({ genre, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 6);
  }, [likedMovies]);

  /* Featured movie for Billboard */
  const featured = useMemo(() => {
    if (backendFeed?.rows?.[0]?.items?.[0]) {
      return normalizeMovie(backendFeed.rows[0].items[0]);
    }
    return moviesList.find((m) => m.rating >= 8.5) || moviesList[0];
  }, [backendFeed, moviesList]);

  return (
    <div>
      <style>{STYLES}</style>

      {/* ── Intro Film Countdown ── */}
      {showIntro && (
        <div className="intro-overlay">
          <span className="intro-num n3">3</span>
          <span className="intro-num n2">2</span>
          <span className="intro-num n1">1</span>
        </div>
      )}

      {/* ── Ambience Overlays ── */}
      <div className="grain-fixed" style={{ backgroundImage: C.bg }} />
      <div className="vignette-overlay" />
      <div ref={spotlightRef} className="spotlight" />

      {/* ── Top Navigation Header ── */}
      <header
        style={{
          borderBottom: `1px solid ${C.border}`,
          position: "sticky",
          top: 0,
          background: "rgba(27,21,31,0.92)",
          backdropFilter: "blur(14px)",
          zIndex: 40,
        }}
      >
        <div
          style={{
            maxWidth: "80rem",
            margin: "0 auto",
            padding: "0 1.5rem",
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          {/* Brand Logo */}
          <div
            className="logo"
            onClick={() => setActiveTab("discover")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              cursor: "pointer",
            }}
          >
            <Clapperboard className="logo-icon" size={24} color={C.accent} />
            <span
              className="font-display"
              style={{
                fontSize: "1.75rem",
                color: C.text,
                letterSpacing: "-0.03em",
                lineHeight: 1,
              }}
            >
              CINESENSE
            </span>
          </div>

          {/* Navigation Links */}
          <nav style={{ display: "flex", alignItems: "center", gap: 28 }}>
            <button
              onClick={() => setActiveTab("discover")}
              className={`nav-link${activeTab === "discover" ? " active" : ""}`}
              style={{
                background: "none",
                border: "none",
                color: activeTab === "discover" ? C.text : C.muted,
                fontFamily: "'Work Sans', sans-serif",
                fontSize: "0.875rem",
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              Discover
            </button>
            <button
              onClick={() => setActiveTab("movies")}
              className={`nav-link${activeTab === "movies" ? " active" : ""}`}
              style={{
                background: "none",
                border: "none",
                color: activeTab === "movies" ? C.text : C.muted,
                fontFamily: "'Work Sans', sans-serif",
                fontSize: "0.875rem",
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              Browse
            </button>
            <button
              onClick={() => setActiveTab("watchlist")}
              className={`nav-link${activeTab === "watchlist" ? " active" : ""}`}
              style={{
                background: "none",
                border: "none",
                color: activeTab === "watchlist" ? C.text : C.muted,
                fontFamily: "'Work Sans', sans-serif",
                fontSize: "0.875rem",
                fontWeight: 500,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <Heart
                size={14}
                fill={likedIds.size > 0 ? C.accent : "none"}
                color={likedIds.size > 0 ? C.accent : C.muted}
              />
              My List
              {likedIds.size > 0 && (
                <span
                  style={{
                    background: C.accent,
                    color: C.bg,
                    borderRadius: "99px",
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    padding: "1px 6px",
                  }}
                >
                  {likedIds.size}
                </span>
              )}
            </button>
          </nav>

          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            {/* Movie Comparison Button */}
            <button
              onClick={() => {
                setCompareMovieA(null);
                setCompareMovieB(null);
                setIsCompareOpen(true);
              }}
              className="ghost-btn"
              title="Compare two movies head-to-head"
              style={{
                background: "transparent",
                border: `1px solid ${C.border}`,
                color: C.text,
                padding: "6px 11px",
                borderRadius: 2,
                fontSize: "0.78rem",
                fontWeight: 500,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 5,
                fontFamily: "'Work Sans', sans-serif",
              }}
            >
              <ArrowRightLeft size={13} color={C.accent} />
              Compare
            </button>

            {/* Watch Tonight Wizard Button */}
            <button
              onClick={() => setIsWatchTonightOpen(true)}
              className="ghost-btn"
              title="4-step decision wizard for tonight's watch"
              style={{
                background: "transparent",
                border: `1px solid ${C.border}`,
                color: C.text,
                padding: "6px 11px",
                borderRadius: 2,
                fontSize: "0.78rem",
                fontWeight: 500,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 5,
                fontFamily: "'Work Sans', sans-serif",
              }}
            >
              <Compass size={13} color={C.accent} />
              Watch Tonight
            </button>

            {/* Movie Night Group Button */}
            <button
              onClick={() => setIsMovieNightOpen(true)}
              className="ghost-btn"
              title="AI Group Consensus with Least Misery"
              style={{
                background: "transparent",
                border: `1px solid ${C.border}`,
                color: C.text,
                padding: "6px 11px",
                borderRadius: 2,
                fontSize: "0.78rem",
                fontWeight: 500,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 5,
                fontFamily: "'Work Sans', sans-serif",
              }}
            >
              <Users size={13} color={C.accent} />
              Movie Night
            </button>

            {/* Evaluation & Benchmarks Button */}
            <button
              onClick={() => setIsEvalOpen(true)}
              className="ghost-btn"
              title="View Offline RecSys & GenAI Benchmarks"
              style={{
                background: "rgba(79,124,116,0.12)",
                border: "1px solid rgba(79,124,116,0.35)",
                color: "#88d3c5",
                padding: "6px 11px",
                borderRadius: 2,
                fontSize: "0.78rem",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 5,
                fontFamily: "'Work Sans', sans-serif",
              }}
            >
              <Award size={13} color="#88d3c5" />
              Benchmarks
            </button>

            {/* AI Assistant Chat Button */}
            <button
              onClick={() => setIsChatOpen(true)}
              className="cta-btn"
              style={{
                background: C.accent,
                color: C.bg,
                border: "none",
                padding: "6px 13px",
                borderRadius: 2,
                fontSize: "0.8rem",
                fontWeight: 700,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
                fontFamily: "'Work Sans', sans-serif",
              }}
            >
              <Sparkles size={14} />
              AI Assistant
            </button>

            {/* Quick Filter Action Button */}
            <button
              onClick={() => setIsAiMode((v) => !v)}
              className="ghost-btn"
              style={{
                background: isAiMode ? C.accentDim : "transparent",
                border: `1px solid ${isAiMode ? C.accent : C.border}`,
                color: isAiMode ? C.accent : C.text,
                padding: "7px 14px",
                borderRadius: 2,
                fontSize: "0.8rem",
                fontWeight: 500,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
                fontFamily: "'Work Sans', sans-serif",
              }}
            >
              <Zap size={14} color={isAiMode ? C.accent : C.muted} />
              Quick Filter
            </button>

            {/* User Cloud Account Button (Phase 2) */}
            {currentUser ? (
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div
                  title={`Logged in as ${currentUser.username} (${currentUser.email})`}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "4px 10px",
                    background: "rgba(227, 163, 78, 0.12)",
                    border: `1px solid ${C.accent}`,
                    borderRadius: 20,
                    color: C.accent,
                    fontSize: "0.78rem",
                    fontWeight: 600,
                  }}
                >
                  <div
                    style={{
                      width: 18,
                      height: 18,
                      borderRadius: "50%",
                      background: C.accent,
                      color: C.bg,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "0.7rem",
                      fontWeight: 700,
                    }}
                  >
                    {currentUser.username.charAt(0).toUpperCase()}
                  </div>
                  <span>{currentUser.username}</span>
                  <span style={{ fontSize: "0.7rem", color: C.muted }}>· {likedIds.size} liked</span>
                </div>
                <button
                  onClick={handleSignOut}
                  title="Sign Out"
                  className="ghost-btn"
                  style={{
                    background: "transparent",
                    border: `1px solid ${C.border}`,
                    color: C.muted,
                    padding: "6px 8px",
                    borderRadius: 2,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <LogOut size={13} />
                </button>
              </div>
            ) : (
              <button
                onClick={() => {
                  setAuthMode("login");
                  setIsAuthOpen(true);
                }}
                className="ghost-btn"
                title="Sign in to sync your ratings & favorites"
                style={{
                  background: "transparent",
                  border: `1px solid ${C.accent}`,
                  color: C.accent,
                  padding: "6px 12px",
                  borderRadius: 2,
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 5,
                  fontFamily: "'Work Sans', sans-serif",
                }}
              >
                <UserIcon size={13} color={C.accent} />
                Sign In
              </button>
            )}
          </div>
        </div>

        {/* AI Query Bar Drawer */}
        <div className={`ai-drawer${isAiMode ? " open" : " closed"}`}>
          <div
            style={{
              maxWidth: "80rem",
              margin: "0 auto",
              padding: "16px 1.5rem 20px",
              borderTop: `1px solid ${C.border}`,
              background: C.surface,
            }}
          >
            <form
              onSubmit={handleAiSearch}
              style={{ display: "flex", gap: 10, alignItems: "center" }}
            >
              <div
                style={{
                  position: "relative",
                  flex: 1,
                  display: "flex",
                  alignItems: "center",
                }}
              >
                <Sparkles
                  size={15}
                  color={C.accent}
                  style={{ position: "absolute", left: 12, pointerEvents: "none" }}
                />
                <input
                  type="text"
                  value={aiQuery}
                  onChange={(e) => setAiQuery(e.target.value)}
                  placeholder="Ask anything: 'Mind-bending sci-fi under 2 hours', 'Dark thriller like Parasite'..."
                  style={{
                    width: "100%",
                    background: C.surfaceHigh,
                    border: `1px solid ${C.borderBright}`,
                    color: C.text,
                    padding: "9px 12px 9px 36px",
                    fontSize: "0.85rem",
                    fontFamily: "'Work Sans', sans-serif",
                    outline: "none",
                  }}
                />
              </div>
              <button
                type="submit"
                disabled={aiLoading}
                className="cta-btn"
                style={{
                  background: C.accent,
                  color: C.bg,
                  border: "none",
                  padding: "9px 18px",
                  fontSize: "0.82rem",
                  fontWeight: 700,
                  fontFamily: "'Work Sans', sans-serif",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  whiteSpace: "nowrap",
                }}
              >
                {aiLoading ? (
                  <Loader2
                    size={15}
                    style={{ animation: "rotateSlow 1s linear infinite" }}
                  />
                ) : (
                  <ArrowRight size={15} />
                )}
                Search
              </button>
            </form>
            {aiResponse?.intro && (
              <p
                style={{
                  marginTop: 12,
                  fontSize: "0.82rem",
                  color: C.text,
                  lineHeight: 1.6,
                  borderTop: `1px solid ${C.border}`,
                  paddingTop: 10,
                }}
              >
                {aiResponse.intro}
                {aiResponse.caveats?.length > 0 && (
                  <em style={{ color: C.muted, marginLeft: 6 }}>
                    ({aiResponse.caveats[0]})
                  </em>
                )}
              </p>
            )}
          </div>
        </div>
      </header>

      {/* ── Scrolling Ticker Banner ── */}
      <Ticker movies={moviesList.filter((m) => m.rating >= 8.5).slice(0, 12)} />

      {/* ══ DISCOVER TAB ══ */}
      {activeTab === "discover" && (
        <>
          {/* Full-width Billboard Hero */}
          <BillboardHero
            featured={featured}
            heroReady={heroReady}
            liked={likedIds.has(featured?.id)}
            onToggleLike={toggleLike}
            onOpenDetails={handleOpenMovie}
          />

          {/* Taste Profile Visualization */}
          <TasteProfile
            likedCount={likedMovies.length}
            tasteData={tasteData}
          />

          {/* ── Dynamic Session-Tuned Carousel (Phase 4) ── */}
          {sessionTunedRecs.length > 0 && (
            <section
              style={{
                maxWidth: "80rem",
                margin: "0 auto",
                padding: "2rem 1.5rem",
                background: "rgba(227, 163, 78, 0.03)",
                borderTop: `1px solid ${C.borderBright}`,
                borderBottom: `1px solid ${C.borderBright}`,
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  justifyContent: "space-between",
                  marginBottom: 18,
                }}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <Sparkles size={18} color={C.accent} />
                    <h2
                      className="font-display"
                      style={{
                        fontSize: "1.75rem",
                        color: C.text,
                        letterSpacing: "-0.02em",
                        margin: 0,
                      }}
                    >
                      Tuned to Your Current Session
                    </h2>
                  </div>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      color: C.accent,
                      letterSpacing: "0.06em",
                      textTransform: "uppercase",
                      marginTop: 4,
                      display: "block",
                    }}
                  >
                    Real-time Candidate Boost from Recent Interactions
                  </span>
                </div>
              </div>
              <div
                className="no-scrollbar"
                style={{
                  display: "flex",
                  gap: 16,
                  overflowX: "auto",
                  paddingBottom: 12,
                }}
              >
                {sessionTunedRecs.map((norm, i) => (
                  <MovieCard
                    key={norm.id}
                    movie={norm}
                    liked={likedIds.has(norm.id)}
                    onToggleLike={toggleLike}
                    onOpen={handleOpenMovie}
                    compact
                    delay={Math.min(i * 40, 300)}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Dynamic Feed Rows */}
          {backendFeed?.rows?.map((row, rIdx) => (
            <section
              key={rIdx}
              style={{
                maxWidth: "80rem",
                margin: "0 auto",
                padding: "2rem 1.5rem",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  justifyContent: "space-between",
                  marginBottom: 18,
                }}
              >
                <div>
                  <h2
                    className="font-display"
                    style={{
                      fontSize: "1.75rem",
                      color: C.text,
                      letterSpacing: "-0.02em",
                    }}
                  >
                    {row.title}
                  </h2>
                  {row.strategy && (
                    <span
                      style={{
                        fontSize: "0.7rem",
                        color: C.teal,
                        letterSpacing: "0.06em",
                        textTransform: "uppercase",
                      }}
                    >
                      {row.strategy.replace(/_/g, " ")}
                    </span>
                  )}
                </div>
              </div>
              <div
                className="no-scrollbar"
                style={{
                  display: "flex",
                  gap: 16,
                  overflowX: "auto",
                  paddingBottom: 12,
                }}
              >
                {row.items?.map((m, i) => {
                  const norm = normalizeMovie(m);
                  return (
                    <MovieCard
                      key={norm.id}
                      movie={norm}
                      liked={likedIds.has(norm.id)}
                      onToggleLike={toggleLike}
                      onOpen={handleOpenMovie}
                      compact
                      delay={Math.min(i * 40, 300)}
                    />
                  );
                })}
              </div>
            </section>
          ))}

          {/* ── Upcoming Theatrical Releases Carousel (Phase 3) ── */}
          {upcomingMovies.length > 0 && (
            <section
              style={{
                maxWidth: "80rem",
                margin: "0 auto",
                padding: "2rem 1.5rem",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  justifyContent: "space-between",
                  marginBottom: 18,
                }}
              >
                <div>
                  <h2
                    className="font-display"
                    style={{
                      fontSize: "1.75rem",
                      color: C.text,
                      letterSpacing: "-0.02em",
                    }}
                  >
                    Upcoming Theatrical & Streaming Releases
                  </h2>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      color: C.teal,
                      letterSpacing: "0.06em",
                      textTransform: "uppercase",
                    }}
                  >
                    TMDB Official Coming Soon Feed
                  </span>
                </div>
              </div>
              <div
                className="no-scrollbar"
                style={{
                  display: "flex",
                  gap: 16,
                  overflowX: "auto",
                  paddingBottom: 12,
                }}
              >
                {upcomingMovies.map((norm, i) => (
                  <MovieCard
                    key={norm.id}
                    movie={norm}
                    liked={likedIds.has(norm.id)}
                    onToggleLike={toggleLike}
                    onOpen={handleOpenMovie}
                    compact
                    delay={Math.min(i * 40, 300)}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Popular Classics Grid (if no backend rows) */}
          {(!backendFeed || backendFeed.rows?.length === 0) && (
            <section
              style={{
                maxWidth: "80rem",
                margin: "0 auto",
                padding: "2rem 1.5rem",
              }}
            >
              <h2
                className="font-display"
                style={{
                  fontSize: "1.75rem",
                  color: C.text,
                  letterSpacing: "-0.02em",
                  marginBottom: 18,
                }}
              >
                Top Rated Cinema
              </h2>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(auto-fill, minmax(155px, 1fr))",
                  gap: "28px 20px",
                }}
              >
                {moviesList.slice(0, 12).map((m, i) => (
                  <Reveal key={m.id} index={i}>
                    <MovieCard
                      movie={m}
                      liked={likedIds.has(m.id)}
                      onToggleLike={toggleLike}
                      onOpen={setSelectedMovie}
                      delay={Math.min(i * 35, 300)}
                    />
                  </Reveal>
                ))}
              </div>
            </section>
          )}
        </>
      )}

      {/* ══ BROWSE TAB ══ */}
      {activeTab === "movies" && (
        <>
          <section
            style={{
              maxWidth: "80rem",
              margin: "0 auto",
              padding: "2rem 1.5rem 1rem",
            }}
          >
            {/* Search and Filters Bar */}
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: 12,
                alignItems: "center",
                marginBottom: 20,
              }}
            >
              <div
                style={{
                  position: "relative",
                  flex: "1 1 240px",
                  display: "flex",
                  alignItems: "center",
                }}
              >
                <Search
                  size={15}
                  color={C.muted}
                  style={{
                    position: "absolute",
                    left: 10,
                    pointerEvents: "none",
                  }}
                />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    setGridKey((k) => k + 1);
                  }}
                  placeholder="Filter by title, director, or keyword..."
                  style={{
                    width: "100%",
                    background: C.surface,
                    border: `1px solid ${C.border}`,
                    color: C.text,
                    padding: "8px 12px 8px 32px",
                    fontSize: "0.85rem",
                    fontFamily: "'Work Sans', sans-serif",
                    outline: "none",
                  }}
                />
              </div>

              {/* Sort selector */}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                style={{
                  background: C.surface,
                  border: `1px solid ${C.border}`,
                  color: C.text,
                  padding: "8px 12px",
                  fontSize: "0.82rem",
                  fontFamily: "'Work Sans', sans-serif",
                  outline: "none",
                  cursor: "pointer",
                }}
              >
                <option value="rating">Sort by Rating</option>
                <option value="year">Sort by Release Year</option>
                <option value="title">Sort Alphabetically</option>
              </select>

              {/* Min rating slider */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  fontSize: "0.78rem",
                  color: C.muted,
                }}
              >
                <span>Min Rating:</span>
                <input
                  type="range"
                  min="0"
                  max="9.5"
                  step="0.5"
                  value={minRating}
                  onChange={(e) => {
                    setMinRating(+e.target.value);
                    setGridKey((k) => k + 1);
                  }}
                  className="rating-range"
                  style={{ width: 90 }}
                />
                <span
                  style={{
                    color: C.accent,
                    fontWeight: 700,
                    minWidth: 24,
                  }}
                >
                  {minRating > 0 ? minRating : "Any"}
                </span>
              </div>
            </div>

            {/* Genre Pills */}
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: 6,
                marginBottom: 28,
              }}
            >
              {availableGenres.map((g) => {
                const active = activeGenres.has(g);
                return (
                  <GenreChip
                    key={g}
                    genre={g}
                    active={active}
                    onClick={() => {
                      setActiveGenres((prev) => {
                        const next = new Set(prev);
                        if (next.has(g)) next.delete(g);
                        else next.add(g);
                        return next;
                      });
                      setGridKey((k) => k + 1);
                    }}
                  />
                );
              })}
              {(activeGenres.size > 0 || minRating > 0 || query) && (
                <button
                  onClick={() => {
                    setActiveGenres(new Set());
                    setMinRating(0);
                    setQuery("");
                    setGridKey((k) => k + 1);
                  }}
                  style={{
                    background: "none",
                    border: `1px solid ${C.border}`,
                    color: C.muted,
                    padding: "4px 12px",
                    fontSize: "0.78rem",
                    cursor: "pointer",
                    fontFamily: "'Work Sans', sans-serif",
                    transition: "border-color 0.2s, color 0.2s",
                  }}
                >
                  Clear filters
                </button>
              )}
            </div>

            {/* Movie Catalog Grid */}
            {filteredBrowse.length === 0 ? (
              <div
                style={{
                  padding: "64px 0",
                  textAlign: "center",
                  color: C.muted,
                }}
              >
                <Film
                  size={36}
                  color={C.border}
                  style={{ marginBottom: 16 }}
                />
                <p>No titles match these filters.</p>
                <p style={{ fontSize: "0.8rem", marginTop: 6 }}>
                  Try widening your search or clearing a genre.
                </p>
              </div>
            ) : (
              <div
                key={gridKey}
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(auto-fill, minmax(155px, 1fr))",
                  gap: "28px 20px",
                }}
              >
                {filteredBrowse.map((m, i) => (
                  <Reveal key={m.id} index={i}>
                    <MovieCard
                      movie={m}
                      liked={likedIds.has(m.id)}
                      onToggleLike={toggleLike}
                      onOpen={setSelectedMovie}
                      delay={Math.min(i * 30, 400)}
                    />
                  </Reveal>
                ))}
              </div>
            )}
          </section>
        </>
      )}

      {/* ══ WATCHLIST TAB ══ */}
      {activeTab === "watchlist" && (
        <section
          style={{
            maxWidth: "80rem",
            margin: "0 auto",
            padding: "3rem 1.5rem",
          }}
          className="fade-in"
        >
          <div style={{ marginBottom: 28 }}>
            <h2
              className="font-display"
              style={{
                fontSize: "2rem",
                color: C.text,
                letterSpacing: "-0.02em",
                marginBottom: 6,
              }}
            >
              My List
            </h2>
            <p style={{ fontSize: "0.82rem", color: C.muted }}>
              Titles you've saved shape the recommendations on Discover.
            </p>
          </div>
          {likedMovies.length === 0 ? (
            <div
              style={{
                padding: "80px 0",
                textAlign: "center",
                color: C.muted,
              }}
            >
              <Heart
                size={42}
                color={C.border}
                style={{ marginBottom: 20 }}
              />
              <p style={{ fontSize: "1rem", marginBottom: 8 }}>
                Your list is empty.
              </p>
              <p style={{ fontSize: "0.82rem", marginBottom: 24 }}>
                Start liking films to build your collection.
              </p>
              <button
                onClick={() => setActiveTab("discover")}
                className="cta-btn"
                style={{
                  background: C.accent,
                  color: C.bg,
                  border: "none",
                  padding: "11px 24px",
                  fontSize: "0.875rem",
                  fontWeight: 700,
                  fontFamily: "'Work Sans', sans-serif",
                  cursor: "pointer",
                }}
              >
                Browse Films
              </button>
            </div>
          ) : (
            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(auto-fill, minmax(155px, 1fr))",
                gap: "28px 20px",
              }}
            >
              {likedMovies.map((m, i) => (
                <Reveal key={m.id} index={i}>
                  <MovieCard
                    movie={m}
                    liked
                    onToggleLike={toggleLike}
                    onOpen={setSelectedMovie}
                    delay={i * 35}
                  />
                </Reveal>
              ))}
            </div>
          )}
        </section>
      )}

      {/* ── Footer ── */}
      <footer
        style={{
          borderTop: `1px solid ${C.border}`,
          maxWidth: "80rem",
          margin: "0 auto",
          padding: "2.5rem 1.5rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Clapperboard size={15} color={C.accent} />
          <span style={{ fontSize: "0.75rem", color: C.muted }}>
            CineSense — AI-Powered Cinema Discovery
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 7,
              height: 7,
              borderRadius: "50%",
              background: connected ? "#4ade80" : C.accent,
              display: "inline-block",
              boxShadow: connected ? "0 0 6px #4ade80" : "none",
            }}
          />
          <span style={{ fontSize: "0.72rem", color: C.muted }}>
            {connected ? "CineSense RecSys Connected" : "Catalog Mode"}
          </span>
        </div>
      </footer>

      {/* ══ DETAIL DRAWER ══ */}
      <MovieDrawer
        selectedMovie={selectedMovie}
        onClose={() => setSelectedMovie(null)}
        liked={likedIds.has(selectedMovie?.id)}
        onToggleLike={toggleLike}
        similarList={similarList}
        loadingSimilar={loadingSimilar}
        onSelectMovie={handleOpenMovie}
        onOpenCompare={(movie) => {
          setCompareMovieA(movie);
          setCompareMovieB(null);
          setIsCompareOpen(true);
        }}
        userRating={selectedMovie ? userRatings[selectedMovie.id] : null}
        onRateMovie={handleRateMovie}
      />

      {/* ══ AI ASSISTANT CHAT MODAL ══ */}
      <ChatModal
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        onOpenDetails={(movie) => {
          handleOpenMovie(movie);
          setIsChatOpen(false);
        }}
        likedIds={likedIds}
        onToggleLike={toggleLike}
      />

      {/* ══ HEAD-TO-HEAD MOVIE COMPARISON MODAL ══ */}
      <MovieComparisonModal
        isOpen={isCompareOpen}
        onClose={() => setIsCompareOpen(false)}
        initialMovieA={compareMovieA}
        initialMovieB={compareMovieB}
        onSelectMovieForDrawer={(movie) => {
          handleOpenMovie(movie);
          setIsCompareOpen(false);
        }}
      />

      {/* ══ WHAT SHOULD I WATCH TONIGHT DECISION WIZARD ══ */}
      <WatchTonightModal
        isOpen={isWatchTonightOpen}
        onClose={() => setIsWatchTonightOpen(false)}
        onSelectMovieForDrawer={(movie) => {
          handleOpenMovie(movie);
          setIsWatchTonightOpen(false);
        }}
      />

      {/* ══ AI GROUP MOVIE NIGHT CONSENSUS MODAL ══ */}
      <MovieNightModal
        isOpen={isMovieNightOpen}
        onClose={() => setIsMovieNightOpen(false)}
        onSelectMovieForDrawer={(movie) => {
          handleOpenMovie(movie);
          setIsMovieNightOpen(false);
        }}
      />

      {/* ══ MODEL BENCHMARKS & EVALUATION DASHBOARD MODAL ══ */}
      <EvaluationDashboardModal
        isOpen={isEvalOpen}
        onClose={() => setIsEvalOpen(false)}
      />

      {/* ══ AUTHENTICATION MODAL (PHASE 2) ══ */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        initialMode={authMode}
        onAuthSuccess={handleAuthSuccess}
      />
    </div>
  );
}
