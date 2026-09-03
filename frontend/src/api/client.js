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

export async function getPopularMovies(k = 20) {
  return fetchApi(`/movies/popular?k=${k}`);
}

export async function getForYouFeed() {
  return fetchApi(`/recommendations/for-you`);
}

export async function searchMovies(q, limit = 20) {
  return fetchApi(`/movies/search?q=${encodeURIComponent(q)}&limit=${limit}`);
}

export async function getMovieDetail(movieId) {
  return fetchApi(`/movies/${movieId}`);
}

export async function getSimilarMovies(movieId, k = 12) {
  return fetchApi(`/movies/${movieId}/similar?k=${k}`);
}

export async function performRagSearch(query, k = 12) {
  return fetchApi(`/ai/search`, {
    method: "POST",
    body: JSON.stringify({ query, k }),
  });
}

export async function getColdStartMovies(k = 20) {
  return fetchApi(`/recommendations/cold-start?k=${k}`);
}

export async function upsertRating(movieId, rating) {
  return fetchApi(`/users/me/ratings/${movieId}`, {
    method: "PUT",
    body: JSON.stringify({ rating }),
  });
}
