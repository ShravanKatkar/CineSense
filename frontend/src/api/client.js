const API_BASE = "/api/v1";

export async function fetchApi(endpoint, options = {}) {
  const token = localStorage.getItem("cinesense_token");
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData?.error?.message || `HTTP error ${response.status}`);
  }

  return response.json();
}

export async function getPopularMovies(k = 28) {
  return fetchApi(`/movies/popular?k=${k}`);
}

export async function getTrendingMovies(timeWindow = "week") {
  return fetchApi(`/movies/trending?time_window=${timeWindow}`);
}


export async function getForYouFeed() {
  return fetchApi(`/recommendations/for-you`);
}

export async function searchMovies(q, limit = 28) {
  return fetchApi(`/movies/search?q=${encodeURIComponent(q)}&limit=${limit}`);
}

export async function getMovieDetail(movieId) {
  return fetchApi(`/movies/${movieId}`);
}

export async function getSimilarMovies(movieId, k = 8) {
  return fetchApi(`/movies/${movieId}/similar?k=${k}`);
}

export async function listGenres() {
  return fetchApi(`/movies/meta/genres`);
}

export async function listMovies({ genre, sort_by = "popularity", page = 1, page_size = 40 } = {}) {
  const params = new URLSearchParams();
  if (genre) params.append("genre", genre);
  if (sort_by) params.append("sort_by", sort_by);
  params.append("page", page);
  params.append("page_size", page_size);
  return fetchApi(`/movies?${params.toString()}`);
}

export async function performRagSearch(query, k = 10) {
  return fetchApi(`/ai/search`, {
    method: "POST",
    body: JSON.stringify({ query, k }),
  });
}

export async function getColdStartMovies(k = 20) {
  return fetchApi(`/recommendations/cold-start?k=${k}`);
}

export async function getFavorites() {
  return fetchApi(`/users/me/favorites`);
}

export async function addFavorite(movieId) {
  return fetchApi(`/users/me/favorites/${movieId}`, { method: "POST" });
}

export async function removeFavorite(movieId) {
  return fetchApi(`/users/me/favorites/${movieId}`, { method: "DELETE" });
}

export async function getMyProfile() {
  return fetchApi(`/users/me/profile`);
}

export async function compareMovies(movieIdA, movieIdB) {
  return fetchApi(`/movies/compare`, {
    method: "POST",
    body: JSON.stringify({ movie_id_a: movieIdA, movie_id_b: movieIdB }),
  });
}

export async function getWatchTonightRecs({ available_time = "standard", mood = "thrilling", company = "solo", language = "any" } = {}) {
  return fetchApi(`/recommendations/wizard`, {
    method: "POST",
    body: JSON.stringify({ available_time, mood, company, language }),
  });
}

export async function getMovieNightRecs(participants) {
  return fetchApi(`/recommendations/movie-night`, {
    method: "POST",
    body: JSON.stringify({ participants }),
  });
}

export async function loginUser(email, password) {
  const data = await fetchApi(`/auth/login`, {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  if (data?.access_token) {
    localStorage.setItem("cinesense_token", data.access_token);
  }
  return data;
}

export async function registerUser(email, username, password) {
  const data = await fetchApi(`/auth/register`, {
    method: "POST",
    body: JSON.stringify({ email, username, password }),
  });
  if (data?.access_token) {
    localStorage.setItem("cinesense_token", data.access_token);
  }
  return data;
}

export async function logoutUser() {
  try {
    await fetchApi(`/auth/logout`, { method: "POST" });
  } catch (err) {
    // Ignore network error on logout
  } finally {
    localStorage.removeItem("cinesense_token");
  }
}

export async function getCurrentUser() {
  const token = localStorage.getItem("cinesense_token");
  if (!token) return null;
  return fetchApi(`/auth/me`);
}

export async function getMyRatings() {
  return fetchApi(`/users/me/ratings`);
}

export async function upsertRating(movieId, rating) {
  return fetchApi(`/users/me/ratings/${movieId}`, {
    method: "PUT",
    body: JSON.stringify({ rating }),
  });
}

export async function deleteRating(movieId) {
  return fetchApi(`/users/me/ratings/${movieId}`, {
    method: "DELETE",
  });
}

export async function getMovieVideos(movieId) {
  return fetchApi(`/movies/${movieId}/videos`);
}

export async function getMovieWatchProviders(movieId) {
  return fetchApi(`/movies/${movieId}/watch-providers`);
}

export async function getUpcomingMovies(page = 1) {
  return fetchApi(`/movies/upcoming?page=${page}`);
}

export async function recordInteraction(eventType, movieId, metadata = {}) {
  try {
    return await fetchApi(`/recommendations/feedback`, {
      method: "POST",
      body: JSON.stringify({
        event_type: eventType,
        movie_id: movieId,
        metadata,
        timestamp: new Date().toISOString(),
      }),
    });
  } catch (err) {
    // Non-blocking telemetry
    return null;
  }
}

export async function getEvaluationBenchmarks() {
  return fetchApi(`/evaluation/benchmarks`);
}

export async function getGenAiEvaluation() {
  return fetchApi(`/evaluation/genai`);
}

export async function getFeedbackMetrics() {
  return fetchApi(`/recommendations/feedback/metrics`);
}

export async function getSessionTunedRecs(seedIds = []) {
  return fetchApi(`/recommendations/session-tune`, {
    method: "POST",
    body: JSON.stringify({ seed_ids: seedIds }),
  });
}

export async function getSystemStatus() {
  return fetchApi(`/system/status`);
}

export async function triggerSystemSync() {
  return fetchApi(`/system/sync`, { method: "POST" });
}

export async function clearSystemCache(prefix = "") {
  return fetchApi(`/system/cache/clear?prefix=${encodeURIComponent(prefix)}`, { method: "POST" });
}



