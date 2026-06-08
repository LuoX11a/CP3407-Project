import CarparkCard from "./CarparkCard";

export default function RecommendationList({
  results,
  loading,
  error,
  onRetry,
  selectedId,
  onSelect,
}) {
  return (
    <div className="sidebar-section">
      <h2>Recommendations</h2>

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
          Waiting for location data...
        </div>
      )}

      {results.map((cp) => (
        <CarparkCard
          key={cp.carpark_id}
          carpark={cp}
          selected={selectedId === cp.carpark_id}
          onClick={() => onSelect(cp)}
        />
      ))}
    </div>
  );
}
