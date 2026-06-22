import { useState, useMemo } from "react";
import CarparkCard from "./CarparkCard";

const SORT_OPTIONS = [
  { key: "distance", label: "Distance" },
  { key: "available", label: "Available Lots" },
  { key: "vacancy", label: "Vacancy Rate" },
];

export default function RecommendationList({
  results,
  loading,
  error,
  onRetry,
  selectedId,
  onSelect,
  favourites,
  onToggleFavourite,
  isLoggedIn,
  locationLoading,
}) {
  const [sortBy, setSortBy] = useState("distance");

  const sorted = useMemo(() => {
    const list = [...results];
    switch (sortBy) {
      case "available":
        list.sort((a, b) => (b.available_lots || 0) - (a.available_lots || 0));
        break;
      case "vacancy":
        list.sort((a, b) => (b.predicted_vacancy_rate || 0) - (a.predicted_vacancy_rate || 0));
        break;
      default:
        list.sort((a, b) => (a.distance_m || 0) - (b.distance_m || 0));
    }
    return list;
  }, [results, sortBy]);

  const favIds = useMemo(() => new Set((favourites || []).map((f) => f.carpark_id)), [favourites]);

  return (
    <div className="sidebar-section">
      <div className="section-header">
        <h2>Recommendations</h2>
        {results.length > 0 && (
          <select
            className="sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.key} value={opt.key}>
                Sort by {opt.label}
              </option>
            ))}
          </select>
        )}
      </div>

      {loading && (
        <div className="loading">
          <div className="spinner" />
          Searching nearby carparks...
        </div>
      )}

      {error && (
        <div className="error-box">
          <p>{error}</p>
          {onRetry && <button onClick={onRetry}>Retry</button>}
        </div>
      )}

      {!loading && !error && results.length === 0 && (
        <div className="loading">
          {locationLoading
            ? "Waiting for GPS location..."
            : "No carparks found nearby. Try expanding your search radius."}
        </div>
      )}

      {sorted.map((cp) => (
        <CarparkCard
          key={cp.carpark_id}
          carpark={cp}
          selected={selectedId === cp.carpark_id}
          onClick={() => onSelect(cp)}
          favourited={favIds.has(cp.carpark_id)}
          onToggleFavourite={onToggleFavourite}
          showFavourite={isLoggedIn}
        />
      ))}
    </div>
  );
}
