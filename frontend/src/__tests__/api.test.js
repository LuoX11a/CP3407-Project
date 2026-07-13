import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  fetchRecommendations,
  searchCarparks,
  fetchFavourites,
} from "../services/api";

describe("API Service", () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ results: [] }),
      })
    );
  });

  it("fetchRecommendations constructs correct URL with all params", async () => {
    await fetchRecommendations(1.3521, 103.8198, 5, 3000);

    expect(fetch).toHaveBeenCalledTimes(1);
    const url = fetch.mock.calls[0][0];
    expect(url).toContain("/api/v1/recommend");
    expect(url).toContain("lat=1.3521");
    expect(url).toContain("lng=103.8198");
    expect(url).toContain("n=5");
    expect(url).toContain("radius_m=3000");
  });

  it("fetchRecommendations uses default n=5 and radius=1000", async () => {
    await fetchRecommendations(1.35, 103.81);

    const url = fetch.mock.calls[0][0];
    expect(url).toContain("n=5");
    expect(url).toContain("radius_m=1000");
  });

  it("searchCarparks encodes query param correctly", async () => {
    await searchCarparks("Orchard Road", 10);

    expect(fetch).toHaveBeenCalledTimes(1);
    const url = fetch.mock.calls[0][0];
    expect(url).toContain("/api/v1/carpark/search");
    expect(url).toContain("q=Orchard+Road");
    expect(url).toContain("limit=10");
  });

  it("throws on HTTP error responses", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 500,
        text: () => Promise.resolve("Internal Server Error"),
      })
    );

    await expect(fetchRecommendations(1.35, 103.81)).rejects.toThrow(
      "Internal Server Error"
    );
  });

  it("throws on 404 responses", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 404,
        text: () => Promise.resolve('{"detail":"Not found"}'),
      })
    );

    await expect(searchCarparks("xyznonexistent")).rejects.toThrow();
  });

  it("fetchFavourites calls the correct endpoint", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ favourites: [] }),
      })
    );

    const result = await fetchFavourites();

    expect(fetch).toHaveBeenCalledTimes(1);
    const url = fetch.mock.calls[0][0];
    expect(url).toBe("/api/v1/favourites");
    expect(result).toEqual({ favourites: [] });
  });
});
