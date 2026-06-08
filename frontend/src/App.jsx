import { useState, useEffect, useCallback } from "react";
import MapView from "./components/MapView";
import RecommendationList from "./components/RecommendationList";
import { fetchRecommendations } from "./services/api";

export default function App() {
  const [userLocation, setUserLocation] = useState(null);
  const [locationError, setLocationError] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  // Get user GPS position
  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationError("Geolocation not supported by your browser");
      return;
    }

    const watchId = navigator.geolocation.watchPosition(
      (pos) => {
        setUserLocation([pos.coords.latitude, pos.coords.longitude]);
        setLocationError(null);
      },
      (err) => {
        setLocationError(`Location access denied. Using default Singapore location.`);
        // Fall back to Singapore city center
        setUserLocation([1.3521, 103.8198]);
      },
      { enableHighAccuracy: true, maximumAge: 60000, timeout: 10000 },
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  // Fetch recommendations when userLocation changes
  const loadRecommendations = useCallback(async () => {
    if (!userLocation) return;

    setLoading(true);
    setApiError(null);

    try {
      const data = await fetchRecommendations(
        userLocation[0],
        userLocation[1],
        5,   // n
        1000, // radius_m
      );
      setResults(data.results || []);
      if (data.results?.length > 0 && !selectedId) {
        setSelectedId(data.results[0].carpark_id);
      }
    } catch (e) {
      setApiError(e.message || "Failed to fetch recommendations");
    } finally {
      setLoading(false);
    }
  }, [userLocation, selectedId]);

  useEffect(() => {
    loadRecommendations();
  }, [userLocation]); // reload when location changes

  const handleSelect = useCallback((cp) => {
    setSelectedId(cp.carpark_id);
  }, []);

  return (
    <>
      <header className="header">
        <div>
          <h1>ParkGuideSG</h1>
          <div className="subtitle">Real-time HDB carpark recommendations</div>
        </div>
        <div style={{ fontSize: 12, color: "#888" }}>
          {userLocation
            ? `GPS: ${userLocation[0].toFixed(4)}, ${userLocation[1].toFixed(4)}`
            : locationError || "Acquiring location..."}
        </div>
      </header>

      <div className="layout">
        <div className="map-panel">
          <MapView
            results={results}
            userLocation={userLocation}
            selectedId={selectedId}
            onSelect={handleSelect}
          />
        </div>

        <div className="sidebar">
          <RecommendationList
            results={results}
            loading={loading}
            error={apiError}
            onRetry={loadRecommendations}
            selectedId={selectedId}
            onSelect={handleSelect}
          />
        </div>
      </div>
    </>
  );
}
