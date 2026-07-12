"""Tests for health endpoint."""

from unittest.mock import patch


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        mock_stats = {"carpark_count": 2150, "latest_data_ts": "2026-07-06T14:00:00+08:00"}

        with patch("app.routers.health.query_db_stats", return_value=mock_stats), patch(
            "app.routers.health.is_model_loaded", return_value=True
        ):
            response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["db_connected"] is True
        assert data["model_loaded"] is True
        assert data["carpark_count"] == 2150

    def test_health_returns_degraded_when_db_fails(self, client):
        with patch("app.routers.health.query_db_stats", side_effect=Exception("DB down")), patch(
            "app.routers.health.is_model_loaded", return_value=False
        ):
            response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["db_connected"] is False
        assert data["model_loaded"] is False
        assert data["carpark_count"] == 0
