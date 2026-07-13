"""Tests for carpark endpoints — search and detail."""


class TestCarparkSearch:
    def test_requires_query_param(self, client):
        """GET /carpark/search without q param → 422."""
        response = client.get("/api/v1/carpark/search")
        assert response.status_code == 422

    def test_returns_matching_carparks(self, client, mock_db):
        """Search with q="Orchard" returns matching results."""
        conn, cur = mock_db
        cur.fetchall.return_value = [
            {
                "carpark_id": "ORC1",
                "address": "Blk 1 Orchard Blvd",
                "car_lots": 300,
                "lat": 1.3040,
                "lng": 103.8318,
                "available_lots": 80,
                "vacancy_rate": 0.267,
            },
            {
                "carpark_id": "ORC2",
                "address": "Blk 5 Orchard Rd",
                "car_lots": 200,
                "lat": 1.3050,
                "lng": 103.8320,
                "available_lots": 15,
                "vacancy_rate": 0.075,
            },
        ]

        response = client.get("/api/v1/carpark/search?q=Orchard&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["results"][0]["carpark_id"] == "ORC1"
        assert data["results"][1]["carpark_id"] == "ORC2"
        # Verify each result has expected fields
        for r in data["results"]:
            assert "carpark_id" in r
            assert "address" in r
            assert "car_lots" in r
            assert "lat" in r
            assert "lng" in r
            assert "available_lots" in r
            # vacancy_rate can be null

    def test_returns_empty_for_no_match(self, client, mock_db):
        """Search with a query matching nothing → empty results array."""
        conn, cur = mock_db
        cur.fetchall.return_value = []

        response = client.get("/api/v1/carpark/search?q=xyznonexistent&limit=20")

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["results"] == []


class TestCarparkDetail:
    def test_404_for_unknown_id(self, client, mock_db):
        """GET /carpark/FAKE with non-existent ID → 404."""
        conn, cur = mock_db
        cur.fetchone.return_value = None  # carpark not found

        response = client.get("/api/v1/carpark/FAKE123")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_returns_carpark_with_history(self, client, mock_db):
        """GET /carpark/ACM returns detail + 24h history."""
        from datetime import datetime, timezone, timedelta
        conn, cur = mock_db
        now = datetime.now(timezone.utc)
        # First call: query_carpark_detail()
        cur.fetchone.return_value = {
            "carpark_id": "ACM",
            "address": "Blk 123 Test Street",
            "car_lots": 400,
            "motorcycle_lots": 50,
            "lat": 1.3521,
            "lng": 103.8198,
            "latest_available": 150,
            "latest_vacancy": 0.375,
            "latest_weather": "Cloudy",
            "latest_updated": now,
        }
        cur.fetchall.return_value = [
            {
                "timestamp": "2026-07-13T13:00:00+08:00",
                "available_lots": 160,
                "vacancy_rate": 0.40,
                "weather_condition": "Cloudy",
            },
            {
                "timestamp": "2026-07-13T12:00:00+08:00",
                "available_lots": 180,
                "vacancy_rate": 0.45,
                "weather_condition": "Fair",
            },
        ]

        response = client.get("/api/v1/carpark/ACM")

        assert response.status_code == 200
        data = response.json()
        # Check carpark detail
        assert "carpark" in data
        assert data["carpark"]["carpark_id"] == "ACM"
        assert data["carpark"]["address"] == "Blk 123 Test Street"
        assert data["carpark"]["car_lots"] == 400
        assert data["carpark"]["motorcycle_lots"] == 50
        assert data["carpark"]["lat"] == 1.3521
        assert data["carpark"]["lng"] == 103.8198
        assert data["carpark"]["latest_available"] == 150
        assert data["carpark"]["latest_vacancy"] == 0.375
        assert data["carpark"]["latest_weather"] == "Cloudy"
        # Check history
        assert "history" in data
        assert len(data["history"]) == 2
        assert data["history"][0]["available_lots"] == 160
        assert data["history"][1]["available_lots"] == 180
