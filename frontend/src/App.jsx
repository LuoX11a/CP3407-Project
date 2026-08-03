import { useState, useEffect, useCallback, useRef } from "react";
import MapView from "./components/MapView";
import RecommendationList from "./components/RecommendationList";
import AuthModal from "./components/AuthModal";
import ErrorBoundary from "./components/ErrorBoundary";
import { fetchRecommendations, searchCarparks, fetchFavourites, addFavourite, removeFavourite, logout } from "./services/api";

const REFRESH_INTERVAL = 60000;

export default function App() {
  const [userLocation, setUserLocation] = useState(null);
  const [locationLoading, setLocationLoading] = useState(true);
  const [locationError, setLocationError] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  const [mode, setMode] = useState("realtime");
  const [forecastTime, setForecastTime] = useState("");

  const [authUser, setAuthUser] = useState(() => {
    const stored = localStorage.getItem("user");
    return stored ? JSON.parse(stored) : null;
  });
  const [showAuth, setShowAuth] = useState(false);
  const [favourites, setFavourites] = useState([]);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);

  const [sheetExpanded, setSheetExpanded] = useState(true);
  const sheetRef = useRef(null);
  const sheetHeight = useRef(0);
  const locationRef = useRef(userLocation);
  locationRef.current = userLocation;

  const isLoggedIn = !!authUser;

  // GPS — once only, no continuous tracking
  useEffect(() => {
    if (!navigator.geolocation) {
      setUserLocation([1.3521, 103.8198]);
      setLocationLoading(false);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLocation([pos.coords.latitude, pos.coords.longitude]);
        setLocationLoading(false);
      },
      () => {
        setUserLocation([1.3521, 103.8198]);
        setLocationLoading(false);
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 },
    );
  }, []);

  useEffect(() => {
    if (isLoggedIn) {
      fetchFavourites().then((d) => setFavourites(d.favourites || [])).catch(() => {});
    } else {
      setFavourites([]);
    }
  }, [isLoggedIn]);

  useEffect(() => {
    if (sheetRef.current) {
      sheetHeight.current = sheetRef.current.offsetHeight;
    }
  }, [sheetExpanded, results]);

  const loadRecommendations = useCallback(async () => {
    const loc = locationRef.current;
    if (!loc) return;
    setLoading(true);
    setApiError(null);
    try {
      const fp = mode === "forecast" && forecastTime ? forecastTime : null;
      const data = await fetchRecommendations(loc[0], loc[1], 8, 3000, fp);
      setResults(data.results || []);
      if (data.results?.length > 0 && !selectedId) {
        setSelectedId(data.results[0].carpark_id);
      }
    } catch (e) {
      setApiError(e.message || "Failed to fetch");
    } finally {
      setLoading(false);
    }
  }, [selectedId, mode, forecastTime]);

  // Initial load + interval — NOT on every state change
  useEffect(() => {
    if (!userLocation) return;
    loadRecommendations();
    const timer = setInterval(loadRecommendations, REFRESH_INTERVAL);
    return () => clearInterval(timer);
  }, [userLocation]);

  // Reload on mode/forecast change
  const prevMode = useRef(mode);
  const prevForecast = useRef(forecastTime);
  useEffect(() => {
    if (prevMode.current !== mode || prevForecast.current !== forecastTime) {
      prevMode.current = mode;
      prevForecast.current = forecastTime;
      loadRecommendations();
    }
  }, [mode, forecastTime, loadRecommendations]);

  const handleSelect = useCallback((cp) => {
    setSelectedId(cp.carpark_id);
    setSheetExpanded(true);
  }, []);

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

  const handleAuth = useCallback((data) => {
    setAuthUser({ id: data.user_id, username: data.username });
    localStorage.setItem("user", JSON.stringify({ id: data.user_id, username: data.username }));
  }, []);

  const handleLogout = useCallback(async () => {
    try { await logout(); } catch {}
    localStorage.removeItem("user");
    setAuthUser(null);
    setFavourites([]);
  }, []);

  const handleToggleFavourite = useCallback(async (cp) => {
    if (!isLoggedIn) { setShowAuth(true); return; }
    const isFav = favourites.some((f) => f.carpark_id === cp.carpark_id);
    try {
      if (isFav) {
        await removeFavourite(cp.carpark_id);
        setFavourites((p) => p.filter((f) => f.carpark_id !== cp.carpark_id));
      } else {
        await addFavourite(cp.carpark_id);
        setFavourites((p) => [...p, { carpark_id: cp.carpark_id, address: cp.address, car_lots: cp.total_lots, lat: cp.lat, lng: cp.lng, available_lots: cp.available_lots, vacancy_rate: cp.predicted_vacancy_rate, weather_condition: cp.weather }]);
      }
    } catch {}
  }, [isLoggedIn, favourites]);

  const handleSearchSelect = useCallback((cp) => {
    setUserLocation([cp.lat, cp.lng]);
    setSelectedId(cp.carpark_id);
    setShowSearchResults(false);
    setSearchQuery("");
  }, []);

  const nowLocal = new Date();
  nowLocal.setMinutes(nowLocal.getMinutes() - nowLocal.getTimezoneOffset());
  const defaultForecastTime = nowLocal.toISOString().slice(0, 16);

  return (
    <ErrorBoundary>
      <div id="app-root">
        <MapView
          results={results}
          userLocation={userLocation}
          selectedId={selectedId}
          onSelect={handleSelect}
          bottomSheetHeight={sheetExpanded ? sheetHeight.current : 0}
        />

        <header className="top-bar">
          <h1 className="app-title">ParkGuideSG</h1>
          <form className="search-form" onSubmit={handleSearch}>
            <input type="text" className="search-input" placeholder="Search address or area..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
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

        <div ref={sheetRef} className={`bottom-sheet ${sheetExpanded ? "expanded" : "collapsed"}`}>
          {/* MODE TOGGLE — big, always visible */}
          <div className="mode-bar">
            <button className={`mode-btn ${mode === "realtime" ? "active" : ""}`} onClick={() => setMode("realtime")}>Now</button>
            <button className={`mode-btn ${mode === "forecast" ? "active" : ""}`} onClick={() => setMode("forecast")}>Plan</button>
            {mode === "forecast" && (
              <input type="datetime-local" className="time-picker" value={forecastTime} onChange={(e) => setForecastTime(e.target.value)} min={defaultForecastTime} />
            )}
          </div>

          <div className="sheet-handle" onClick={() => setSheetExpanded(!sheetExpanded)}>
            <div className="handle-bar" />
            <span className="handle-label">{results.length} carparks — tap to {sheetExpanded ? "collapse" : "expand"}</span>
          </div>

          {sheetExpanded && (
            <div className="sheet-content">
              {showSearchResults && (
                <div className="search-results-panel">
                  <div className="section-header">
                    <h3>Search Results</h3>
                    <button className="btn-close" onClick={() => setShowSearchResults(false)}>&times;</button>
                  </div>
                  {searchResults.length === 0 ? (
                    <p className="no-results">No carparks found</p>
                  ) : (
                    searchResults.map((cp) => (
                      <div key={cp.carpark_id} className="search-result-item" onClick={() => handleSearchSelect(cp)}>
                        <span className="sr-name">{cp.carpark_id}</span>
                        <span className="sr-address">{cp.address}</span>
                        <span className="sr-lots">{cp.available_lots != null ? `${cp.available_lots} available` : ""}</span>
                      </div>
                    ))
                  )}
                </div>
              )}

              {isLoggedIn && favourites.length > 0 && (
                <div className="favourites-panel">
                  <h3>Favourites</h3>
                  {favourites.map((f) => (
                    <div key={f.carpark_id} className="fav-item" onClick={() => handleSearchSelect(f)}>
                      <span className="star">&#9733;</span>
                      <div><div className="fav-name">{f.carpark_id}</div><div className="fav-address">{f.address}</div></div>
                      <button className="btn-remove-fav" onClick={(e) => { e.stopPropagation(); handleToggleFavourite(f); }}>&times;</button>
                    </div>
                  ))}
                </div>
              )}

              <RecommendationList
                results={results} loading={loading} error={apiError} onRetry={loadRecommendations}
                selectedId={selectedId} onSelect={handleSelect}
                favourites={favourites} onToggleFavourite={handleToggleFavourite}
                isLoggedIn={isLoggedIn} locationLoading={locationLoading}
                mode={mode} forecastTime={forecastTime}
              />
            </div>
          )}
        </div>

        {showAuth && <AuthModal onClose={() => setShowAuth(false)} onAuth={handleAuth} />}
      </div>
    </ErrorBoundary>
  );
}
