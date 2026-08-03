import { useState, useEffect, useCallback, useRef } from "react";
import MapView from "./components/MapView";
import RecommendationList from "./components/RecommendationList";
import AuthModal from "./components/AuthModal";
import ErrorBoundary from "./components/ErrorBoundary";
import { fetchRecommendations, searchCarparks, fetchFavourites, addFavourite, removeFavourite, logout } from "./services/api";

const REFRESH_INTERVAL = 60000; // 60 seconds

export default function App() {
  const [userLocation, setUserLocation] = useState(null);
  const [locationLoading, setLocationLoading] = useState(true);
  const [locationError, setLocationError] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  // Mode: "realtime" (show current data) | "forecast" (predict future)
  const [mode, setMode] = useState("realtime");
  const [forecastTime, setForecastTime] = useState("");

  // Auth
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

  // Bottom sheet drag state
  const [sheetExpanded, setSheetExpanded] = useState(true);
  const sheetRef = useRef(null);
  const sheetHeight = useRef(0);

  const isLoggedIn = !!authUser;

  // Get user GPS position
  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationError("Geolocation not supported");
      setUserLocation([1.3521, 103.8198]);
      setLocationLoading(false);
      return;
    }

    const watchId = navigator.geolocation.watchPosition(
      (pos) => {
        setUserLocation([pos.coords.latitude, pos.coords.longitude]);
        setLocationError(null);
        setLocationLoading(false);
      },
      () => {
        setLocationError("Location access denied. Using default Singapore location.");
        setUserLocation([1.3521, 103.8198]);
        setLocationLoading(false);
      },
      { enableHighAccuracy: true, maximumAge: 60000, timeout: 10000 },
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  // Load favourites
  useEffect(() => {
    if (isLoggedIn) {
      fetchFavourites()
        .then((data) => setFavourites(data.favourites || []))
        .catch(() => {});
    } else {
      setFavourites([]);
    }
  }, [isLoggedIn]);

  // Measure bottom sheet height for map offset
  useEffect(() => {
    if (sheetRef.current) {
      sheetHeight.current = sheetRef.current.offsetHeight;
    }
  }, [sheetExpanded, results]);

  // Fetch recommendations
  const loadRecommendations = useCallback(async () => {
    if (!userLocation) return;
    setLoading(true);
    setApiError(null);
    try {
      const forecastParam = mode === "forecast" && forecastTime ? forecastTime : null;
      const data = await fetchRecommendations(userLocation[0], userLocation[1], 8, 3000, forecastParam);
      setResults(data.results || []);
      if (data.results?.length > 0 && !selectedId) {
        setSelectedId(data.results[0].carpark_id);
      }
    } catch (e) {
      setApiError(e.message || "Failed to fetch recommendations");
    } finally {
      setLoading(false);
    }
  }, [userLocation, selectedId, mode, forecastTime]);

  // Initial load + fixed interval refresh
  useEffect(() => {
    loadRecommendations();
    const timer = setInterval(loadRecommendations, REFRESH_INTERVAL);
    return () => clearInterval(timer);
  }, [loadRecommendations]);

  // Reload when mode or forecastTime changes
  useEffect(() => {
    loadRecommendations();
  }, [mode, forecastTime]);

  const handleSelect = useCallback((cp) => {
    setSelectedId(cp.carpark_id);
    setSheetExpanded(true);
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
    const user = { id: data.user_id, username: data.username };
    setAuthUser(user);
    localStorage.setItem("user", JSON.stringify(user));
  }, []);

  const handleLogout = useCallback(async () => {
    try { await logout(); } catch {}
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
    } catch {}
  }, [isLoggedIn, favourites]);

  // Fly to search result
  const handleSearchSelect = useCallback((cp) => {
    setUserLocation([cp.lat, cp.lng]);
    setSelectedId(cp.carpark_id);
    setShowSearchResults(false);
    setSearchQuery("");
  }, []);

  // Get today's default datetime for forecast picker
  const nowLocal = new Date();
  nowLocal.setMinutes(nowLocal.getMinutes() - nowLocal.getTimezoneOffset());
  const defaultForecastTime = nowLocal.toISOString().slice(0, 16);

  return (
    <ErrorBoundary>
      <div id="app-root">
        {/* Map fills everything */}
        <MapView
          results={results}
          userLocation={userLocation}
          selectedId={selectedId}
          onSelect={handleSelect}
          bottomSheetHeight={sheetExpanded ? sheetHeight.current : 0}
        />

        {/* Top bar — search + auth */}
        <header className="top-bar">
          <div className="top-bar-left">
            <h1 className="app-title">ParkGuideSG</h1>
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
          <div className="top-bar-right">
            {isLoggedIn ? (
              <>
                <span className="username">{authUser.username}</span>
                <button onClick={handleLogout} className="btn-logout">Logout</button>
              </>
            ) : (
              <button onClick={() => setShowAuth(true)} className="btn-login">Login</button>
            )}
          </div>
        </header>

        {/* Mode toggle — floating above bottom sheet */}
        <div className="mode-bar">
          <button
            className={`mode-btn ${mode === "realtime" ? "active" : ""}`}
            onClick={() => setMode("realtime")}
          >
            🟢 Now
          </button>
          <button
            className={`mode-btn ${mode === "forecast" ? "active" : ""}`}
            onClick={() => setMode("forecast")}
          >
            🔮 Plan Ahead
          </button>
          {mode === "forecast" && (
            <input
              type="datetime-local"
              className="time-picker"
              value={forecastTime}
              onChange={(e) => setForecastTime(e.target.value)}
              min={defaultForecastTime}
            />
          )}
        </div>

        {/* Bottom sheet — results overlay */}
        <div
          ref={sheetRef}
          className={`bottom-sheet ${sheetExpanded ? "expanded" : "collapsed"}`}
        >
          <div
            className="sheet-handle"
            onClick={() => setSheetExpanded(!sheetExpanded)}
          >
            <div className="handle-bar" />
            <span className="handle-label">
              {results.length} carparks nearby
              {sheetExpanded ? " — tap to collapse" : " — tap to expand"}
            </span>
          </div>

          {sheetExpanded && (
            <div className="sheet-content">
              {/* Search results */}
              {showSearchResults && (
                <div className="search-results-panel">
                  <div className="section-header">
                    <h3>Search Results</h3>
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

              {/* Favourites */}
              {isLoggedIn && favourites.length > 0 && (
                <div className="favourites-panel">
                  <h3>★ Your Favourites</h3>
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

              {/* Recommendations */}
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
                mode={mode}
                forecastTime={forecastTime}
              />
            </div>
          )}
        </div>

        {/* Auth modal */}
        {showAuth && (
          <AuthModal
            onClose={() => setShowAuth(false)}
            onAuth={handleAuth}
          />
        )}
      </div>
    </ErrorBoundary>
  );
}
