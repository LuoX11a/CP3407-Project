import { useEffect, useRef } from "react";
import L from "leaflet";

const SINGAPORE_CENTER = [1.3521, 103.8198];

const markerColors = {
  green:  "#4caf50",
  yellow: "#ff9800",
  red:    "#f44336",
};

function createIcon(color) {
  return L.divIcon({
    className: "",
    html: `<div style="
      width:24px;height:24px;border-radius:50%;
      background:${color};border:3px solid #fff;
      box-shadow:0 2px 6px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -14],
  });
}

function popupContent(cp) {
  const rate = (cp.predicted_vacancy_rate * 100).toFixed(0);
  const navUrl = /iPad|iPhone|iPod/.test(navigator.userAgent)
    ? `https://maps.apple.com/?daddr=${cp.lat},${cp.lng}&dirflg=d`
    : `https://www.google.com/maps/dir/?api=1&destination=${cp.lat},${cp.lng}`;
  return `
    <div class="popup-card">
      <h3>${cp.carpark_id}</h3>
      <div class="popup-stats">
        Available: <span>${cp.available_lots}</span> / ${cp.total_lots} &nbsp;(${rate}%)
      </div>
      <div class="popup-stats">
        Distance: <span>${cp.distance_m}m</span> &nbsp;|&nbsp;
        Weather: <span>${cp.weather}</span>
      </div>
      <div class="popup-stats">
        Status: <span style="color:${markerColors[cp.status?.toLowerCase()] || '#4caf50'}">${cp.status}</span>
      </div>
      <a href="${navUrl}" target="_blank" rel="noopener noreferrer"
         class="popup-nav-link"
         style="display:inline-block;margin-top:8px;padding:6px 12px;
                background:#2196f3;color:#fff;border-radius:6px;
                text-decoration:none;font-weight:600;font-size:13px;">
        Navigate
      </a>
    </div>
  `;
}

export default function MapView({ results, userLocation, selectedId, onSelect, bottomSheetHeight = 0 }) {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markersLayer = useRef(null);
  const userMarker = useRef(null);
  const hasCentered = useRef(false);

  // Init map
  useEffect(() => {
    if (mapInstance.current) return;

    const map = L.map(mapRef.current, {
      center: SINGAPORE_CENTER,
      zoom: 14,
      zoomControl: false,
    });

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> | Data.gov.sg',
      maxZoom: 19,
    }).addTo(map);

    // Zoom control in bottom-right (away from results panel)
    L.control.zoom({ position: "bottomright" }).addTo(map);

    mapInstance.current = map;
    markersLayer.current = L.layerGroup().addTo(map);

    return () => {
      map.remove();
      mapInstance.current = null;
    };
  }, []);

  // Update user marker — center on first location with offset for bottom sheet
  useEffect(() => {
    const map = mapInstance.current;
    if (!map || !userLocation) return;

    if (userMarker.current) {
      userMarker.current.setLatLng(userLocation);
    } else {
      const icon = L.divIcon({
        className: "",
        html: `<div style="
          width:16px;height:16px;border-radius:50%;
          background:#2196f3;border:3px solid #fff;
          box-shadow:0 0 0 4px rgba(33,150,243,0.3);
        "></div>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      });
      userMarker.current = L.marker(userLocation, { icon }).addTo(map)
        .bindPopup("Your location");

      if (!hasCentered.current) {
        map.setView(userLocation, 15);
        // Shift center up so pin is in visible top-half of map
        if (bottomSheetHeight > 0) {
          map.panBy([0, -bottomSheetHeight / 2], { animate: false });
        }
        hasCentered.current = true;
      }
    }
  }, [userLocation, bottomSheetHeight]);

  // Re-center on user
  const handleRecenter = () => {
    const map = mapInstance.current;
    if (!map || !userLocation) return;
    map.setView(userLocation, 15);
    if (bottomSheetHeight > 0) {
      setTimeout(() => map.panBy([0, -bottomSheetHeight / 2]), 10);
    }
  };

  // Update carpark markers
  useEffect(() => {
    const layer = markersLayer.current;
    if (!layer) return;

    layer.clearLayers();

    results.forEach((cp) => {
      const color = markerColors[cp.status?.toLowerCase()] || "#4caf50";
      const icon = createIcon(color);
      const marker = L.marker([cp.lat, cp.lng], { icon })
        .bindPopup(popupContent(cp));

      marker.on("click", () => onSelect(cp));
      layer.addLayer(marker);

      if (cp.carpark_id === selectedId) {
        marker.openPopup();
      }
    });
  }, [results, selectedId, onSelect]);

  return (
    <div ref={mapRef} className="map-container">
      <button
        className="recenter-btn"
        onClick={handleRecenter}
        title="Re-center on my location"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>
        </svg>
      </button>
    </div>
  );
}
