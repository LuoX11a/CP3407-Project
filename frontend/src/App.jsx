import { useState, useEffect, useCallback } from "react";
import MapView from "./components/MapView";
import RecommendationList from "./components/RecommendationList";
import AuthModal from "./components/AuthModal";
import { fetchRecommendations, searchCarparks, fetchFavourites, addFavourite, removeFavourite } from "./services/api";

export default function App() {
  const [userLocation, setUserLocation] = useState(null);
  const [locationLoading, setLocationLoading] = useState(true);
  const [locationError, setLocationError] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  // Auth state
  const [authUser, setAuthUser] = useState(() => {
    const stored = localStorage.getItem("user");
    return stored ? JSON.parse(stored) : null;
  });
  const [showAuth, setShowAuth] = useState(false);

  // Favourites
  const [favourites, setFavourites] = useState([]);

  // Address search
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);

  const isLoggedIn = !!authUser;

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
        setLocationLoading(false);
      },
      (err) => {
        setLocationError("Location access denied. Using default Singapore location.");
        setUserLocation([1.3521, 103.8198]);
        setLocationLoading(false);
      },
      { enableHighAccuracy: true, maximumAge: 60000, timeout: 10000 },
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  // Load favourites when logged in
  useEffect(() => {
    if (isLoggedIn) {
      fetchFavourites()
        .then((data) => setFavourites(data.favourites || []))
        .catch(() => {});
    } else {
      setFavourites([]);
    }
  }, [isLoggedIn]);

  // Fetch recommendations when userLocation changes
  const loadRecommendations = useCallback(async () => {
    if (!userLocation) return;
    setLoading(true);
    setApiError(null);
    try {
      const data = await fetchRecommendations(userLocation[0], userLocation[1], 5, 3000);
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
  }, [userLocation]);

  const handleSelect = useCallback((cp) => {
    setSelectedId(cp.carpark_id);
  }, []);

  // Address search
  const handleSearch = useCallback(async (e) => {
    e.preventDefault();
    const q = searchQuery.trim();
    if (!q) return;
    try {
      const data = await searchCarparks(q);
      setSearchResults(data.results || []);
      setShowSearchResults(true);
    } catch {
      setSearchResults([]);
      setShowSearchResults(true);
    }
  }, [searchQuery]);

  // Auth
  const handleAuth = useCallback((data) => {
    setAuthUser({ id: data.user_id, username: data.username });
  }, []);

  const handleLogout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setAuthUser(null);
    setFavourites([]);
  }, []);

  // Favourites
  const handleToggleFavourite = useCallback(async (cp) => {
    if (!isLoggedIn) {
      setShowAuth(true);
      return;
    }
    const isFav = favourites.some((f) => f.carpark_id === cp.carpark_id);
    try {
      if (isFav) {
        await removeFavourite(cp.carpark_id);
        setFavourites((prev) => prev.filter((f) => f.carpark_id !== cp.carpark_id));
      } else {
        await addFavourite(cp.carpark_id);
        setFavourites((prev) => [
          ...prev,
          { carpark_id: cp.carpark_id, address: cp.address, car_lots: cp.total_lots,
            lat: cp.lat, lng: cp.lng, available_lots: cp.available_lots,
            vacancy_rate: cp.predicted_vacancy_rate, weather_condition: cp.weather },
        ]);
      }
    } catch {
      // silently fail
    }
  }, [isLoggedIn, favourites]);

  // Fly to search result
  const handleSearchSelect = useCallback((cp) => {
    setUserLocation([cp.lat, cp.lng]);
    setSelectedId(cp.carpark_id);
    setShowSearchResults(false);
    setSearchQuery("");
  }, []);

  return (
    <>
      <header className="header">
        <div>
          <h1>ParkGuideSG</h1>
          <div className="subtitle">Real-time HDB carpark recommendations</div>
        </div>

        <form className="search-form" onSubmit={handleSearch}>
          <input
            type="text"
            className="search-input"
            placeholder="Search address or area..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button type="submit" className="search-btn">Search</button>
        </form>

        <div className="header-right">
          <div className="gps-info">
            {locationLoading && !userLocation
              ? "Acquiring GPS location..."
              : userLocation
                ? `GPS: ${userLocation[0].toFixed(4)}, ${userLocation[1].toFixed(4)}`
                : locationError || "Location unavailable"}
          </div>
          {isLoggedIn ? (
            <div className="user-info">
              <span className="username">{authUser.username}</span>
              <button onClick={handleLogout} className="btn-logout">Logout</button>
            </div>
          ) : (
            <button onClick={() => setShowAuth(true)} className="btn-login">Login</button>
          )}
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
          {showSearchResults && (
            <div className="sidebar-section search-results">
              <div className="section-header">
                <h2>Search Results</h2>
                <button className="btn-close" onClick={() => setShowSearchResults(false)}>✕</button>
              </div>
              {searchResults.length === 0 ? (
                <p className="no-results">No carparks found</p>
              ) : (
                searchResults.map((cp) => (
                  <div
                    key={cp.carpark_id}
                    className="search-result-item"
                    onClick={() => handleSearchSelect(cp)}
                  >
                    <span className="sr-name">{cp.carpark_id}</span>
                    <span className="sr-address">{cp.address}</span>
                    <span className="sr-lots">
                      {cp.available_lots != null ? `${cp.available_lots} available` : ""}
                    </span>
                  </div>
                ))
              )}
            </div>
          )}

          {isLoggedIn && favourites.length > 0 && (
            <div className="sidebar-section favourites-section">
              <h2>Your Favourites</h2>
              {favourites.map((f) => (
                <div
                  key={f.carpark_id}
                  className="fav-item"
                  onClick={() => handleSearchSelect(f)}
                >
                  <span className="star">★</span>
                  <div>
                    <div className="fav-name">{f.carpark_id}</div>
                    <div className="fav-address">{f.address}</div>
                  </div>
                  <button
                    className="btn-remove-fav"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleFavourite(f);
                    }}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}

          <RecommendationList
            results={results}
            loading={loading}
            error={apiError}
            onRetry={loadRecommendations}
            selectedId={selectedId}
            onSelect={handleSelect}
            favourites={favourites}
            onToggleFavourite={handleToggleFavourite}
            isLoggedIn={isLoggedIn}
            locationLoading={locationLoading}
          />
        </div>
      </div>

      {showAuth && (
        <AuthModal
          onClose={() => setShowAuth(false)}
          onAuth={handleAuth}
        />
      )}
    </>
  );
}
