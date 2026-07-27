import { useMemo } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
} from "chart.js";
import NavButton from "./NavButton";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip);

function statusBadge(status) {
  const cls = status?.toLowerCase() || "green";
  return <span className={`badge ${cls}`}>{status}</span>;
}

export default function CarparkCard({ carpark, selected, onClick, favourited, onToggleFavourite, showFavourite }) {
  const trendLabels = useMemo(
    () => carpark.trend?.map((p) => p.hour) ?? [],
    [carpark.trend],
  );
  const trendData = useMemo(
    () => carpark.trend?.map((p) => p.rate * 100) ?? [],
    [carpark.trend],
  );

  const chartData = {
    labels: trendLabels,
    datasets: [
      {
        data: trendData,
        borderColor: statusToColor(carpark.status),
        backgroundColor: statusToColor(carpark.status) + "20",
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
      },
    ],
  };

  const chartOpts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { tooltip: { enabled: false }, legend: { display: false } },
    scales: {
      x: { display: false },
      y: { display: false, min: 0, max: 100 },
    },
  };

  return (
    <div
      className={`carpark-card ${selected ? "selected" : ""}`}
      onClick={onClick}
    >
      <div className="card-header">
        <span className="name">
          {showFavourite && (
            <span
              className={`star-btn ${favourited ? "favourited" : ""}`}
              onClick={(e) => {
                e.stopPropagation();
                onToggleFavourite && onToggleFavourite(carpark);
              }}
              title={favourited ? "Remove from favourites" : "Add to favourites"}
            >
              {favourited ? "★" : "☆"}
            </span>
          )}
          {carpark.carpark_id}
        </span>
        <span className="distance">{carpark.distance_m}m</span>
      </div>
      <div className="card-stats">
        <div className="stat">
          <span className="label">Available</span>
          <span className="value">{carpark.available_lots}</span>
        </div>
        <div className="stat">
          <span className="label">Predicted</span>
          <span className="value">{(carpark.predicted_vacancy_rate * 100).toFixed(0)}%</span>
        </div>
        <div className="stat">
          <span className="label">Total Lots</span>
          <span className="value">{carpark.total_lots}</span>
        </div>
        <div className="stat">
          <span className="label">Status</span>
          {statusBadge(carpark.status)}
        </div>
      </div>
      <div className="card-address" title={carpark.address}>
        {carpark.address}
      </div>
      {trendLabels.length > 0 && (
        <div className="trend-chart">
          <Line data={chartData} options={chartOpts} />
        </div>
      )}
      <div className="card-footer">
        <div className="card-meta">
          {carpark.hourly_rate && carpark.hourly_rate !== "N/A" && (
            <span className="rate-tag" title="Hourly parking rate">
              {carpark.hourly_rate}
            </span>
          )}
          {carpark.ev_charging && (
            <span className="ev-tag" title="EV charging available">
              EV
            </span>
          )}
          <span className="card-weather" title={carpark.weather}>
            {carpark.weather || "Unknown"}
          </span>
        </div>
        <NavButton
          lat={carpark.lat}
          lng={carpark.lng}
          address={carpark.address}
          compact
        />
      </div>
    </div>
  );
}

function statusToColor(status) {
  switch (status?.toLowerCase()) {
    case "green":
      return "#4caf50";
    case "yellow":
      return "#ff9800";
    case "red":
      return "#f44336";
    default:
      return "#4caf50";
  }
}
