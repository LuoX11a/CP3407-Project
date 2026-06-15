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
      box-shadow:0 2px 6px rgba(0,0,0,0.5);
    "></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -14],
  });
}

function popupContent(cp) {
  const rate = (cp.predicted_vacancy_rate * 100).toFixed(0);
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
    </div>
  `;
}

export default function MapView({ results, userLocation, selectedId, onSelect }) {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markersLayer = useRef(null);
  const userMarker = useRef(null);
  const hasCentered = useRef(false);

  // Init map once
  useEffect(() => {
    if (mapInstance.current) return;

    const map = L.map(mapRef.current, {
      center: SINGAPORE_CENTER,
      zoom: 14,
      zoomControl: true,
    });

    L.tileLayer("https://www.onemap.gov.sg/maps/tiles/Default/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.onemap.gov.sg">OneMap</a> | Data.gov.sg',
      maxZoom: 19,
    }).addTo(map);

    mapInstance.current = map;
    markersLayer.current = L.layerGroup().addTo(map);

    return () => {
      map.remove();
      mapInstance.current = null;
    };
  }, []);

  // Update user marker — center once on first location, then only update marker
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

      // Center on first location only
      if (!hasCentered.current) {
        map.setView(userLocation, map.getZoom());
        hasCentered.current = true;
      }
    }
  }, [userLocation]);

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

      // Open popup for selected
      if (cp.carpark_id === selectedId) {
        marker.openPopup();
      }
    });
  }, [results, selectedId, onSelect]);

  return <div ref={mapRef} style={{ width: "100%", height: "100%" }} />;
}
