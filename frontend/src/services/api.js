const BASE = "/api/v1";

async function request(path, options = {}) {
  const token = localStorage.getItem("token");
  const headers = { ...options.headers };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}

function authHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── Recommendations ──────────────────────────────────────

export function fetchRecommendations(lat, lng, n = 5, radiusM = 1000) {
  const params = new URLSearchParams({ lat, lng, n, radius_m: radiusM });
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

// ── Favourites ────────────────────────────────────────────

export function fetchFavourites() {
  return request("/favourites", { headers: authHeaders() });
}

export function addFavourite(carparkId) {
  return request(`/favourites/${carparkId}`, {
    method: "POST",
    headers: authHeaders(),
  });
}

export function removeFavourite(carparkId) {
  return request(`/favourites/${carparkId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}
