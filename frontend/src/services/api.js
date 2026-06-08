/**
 * API client for ParkGuideSG backend.
 * In dev mode, Vite proxies /api → localhost:8000.
 */

const BASE = "/api/v1";

async function request(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}

export function fetchRecommendations(lat, lng, n = 5, radiusM = 1000) {
  const params = new URLSearchParams({ lat, lng, n, radius_m: radiusM });
  return request(`/recommend?${params}`);
}

export function fetchCarparkDetail(id) {
  return request(`/carpark/${id}`);
}

export function fetchHealth() {
  return request("/health");
}
