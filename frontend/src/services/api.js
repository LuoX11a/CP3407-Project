const BASE = "/api/v1";

async function request(path, options = {}) {
  // httpOnly cookies are sent automatically by the browser.
  // No manual token management needed.
  // Authorization header kept as fallback for API consumers.
  const headers = { ...options.headers };
  const token = localStorage.getItem("token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Recommendations ──────────────────────────────────────

export function fetchRecommendations(lat, lng, n = 5, radiusM = 1000, forecastTime = null) {
  const params = new URLSearchParams({ lat, lng, n, radius_m: radiusM });
  if (forecastTime) {
    params.set("forecast_time", forecastTime);
  }
  return request(`/recommend?${params}`);
}

// ── Carpark ───────────────────────────────────────────────

export function fetchCarparkDetail(id) {
  return request(`/carpark/${id}`);
}

export function searchCarparks(query, limit = 10) {
  const params = new URLSearchParams({ q: query, limit });
  return request(`/carpark/search?${params}`);
}

// ── Health ────────────────────────────────────────────────

export function fetchHealth() {
  return request("/health");
}

// ── Auth ──────────────────────────────────────────────────

export function register(username, email, password) {
  return request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
}

export function login(username, password) {
  return request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
}

export function logout() {
  return request("/auth/logout", { method: "POST" });
}

// ── Favourites ────────────────────────────────────────────

export function fetchFavourites() {
  return request("/favourites");
}

export function addFavourite(carparkId) {
  return request(`/favourites/${carparkId}`, { method: "POST" });
}

export function removeFavourite(carparkId) {
  return request(`/favourites/${carparkId}`, { method: "DELETE" });
}
