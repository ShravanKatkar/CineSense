import { PALETTE } from "../constants/theme";

export function genreColor(genre = "Cinema") {
  let h = 0;
  for (let i = 0; i < genre.length; i++) h = genre.charCodeAt(i) + ((h << 5) - h);
  return PALETTE[Math.abs(h) % PALETTE.length];
}

export function shade(hex, pct) {
  const n = parseInt(hex.slice(1), 16);
  const clamp = (v) => Math.max(0, Math.min(255, v));
  const r = clamp((n >> 16) + Math.round(2.55 * pct));
  const g = clamp(((n >> 8) & 0xff) + Math.round(2.55 * pct));
  const b = clamp((n & 0xff) + Math.round(2.55 * pct));
  return `#${(0x1000000 + r * 0x10000 + g * 0x100 + b).toString(16).slice(1)}`;
}

export function normalizeMovie(m) {
  if (!m) return null;

  // Genres — backend sends either .genres (TMDB path) or .genre_names (parquet path)
  const genres =
    (Array.isArray(m.genres) && m.genres.length > 0 ? m.genres : null) ||
    (Array.isArray(m.genre_names) && m.genre_names.length > 0 ? m.genre_names : null) ||
    ["Cinema"];

  // Year
  let year = m.release_year || m.year;
  if (!year && m.release_date) {
    const p = new Date(m.release_date).getFullYear();
    if (!isNaN(p)) year = p;
  }

  // Director — TMDB detail sends .directors array; list endpoints don't include it
  const director =
    m.director ||
    (Array.isArray(m.directors) && m.directors.length > 0 ? m.directors.join(", ") : null) ||
    (Array.isArray(m.director_names) && m.director_names.length > 0 ? m.director_names.join(", ") : "Various");

  // Rating — TMDB uses vote_average (0-10)
  const rating =
    typeof m.vote_average === "number" ? +m.vote_average.toFixed(1) :
    typeof m.weighted_rating === "number" ? +m.weighted_rating.toFixed(1) :
    typeof m.rating === "number" ? +m.rating.toFixed(1) : 7.5;

  // Poster URL — backend already computes poster_url from poster_path
  const poster_url =
    m.poster_url ||
    (m.poster_path && !m.poster_path.includes("placeholder")
      ? (m.poster_path.startsWith("http") ? m.poster_path : `https://image.tmdb.org/t/p/w342${m.poster_path}`)
      : null);

  const backdrop_url =
    m.backdrop_url ||
    (m.backdrop_path && !m.backdrop_path.includes("placeholder")
      ? (m.backdrop_path.startsWith("http") ? m.backdrop_path : `https://image.tmdb.org/t/p/w1280${m.backdrop_path}`)
      : null);

  return {
    id: m.id || m.tmdb_id || m.movie_id || Math.random(),
    tmdb_id: m.tmdb_id || m.id || null,
    title: m.title || "Untitled",
    year: year || 2020,
    director,
    runtime: m.runtime || null,
    rating,
    genres,
    blurb: m.overview || m.blurb || m.tagline || "An evocative cinematic journey.",
    poster_url: poster_url && poster_url !== "" ? poster_url : null,
    backdrop_url: backdrop_url && backdrop_url !== "" ? backdrop_url : null,
    reason: m.reason || null,
    popularity: m.popularity || 0,
  };
}
