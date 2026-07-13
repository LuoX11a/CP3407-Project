"""Tests for favourites CRUD endpoints — list, add, remove."""

from app.services.auth import create_token


class TestFavouritesList:
    def test_requires_auth(self, client):
        """GET /favourites without auth token → 401."""
        response = client.get("/api/v1/favourites")
        assert response.status_code == 401

    def test_returns_empty_for_new_user(self, client, mock_db, auth_headers):
        """Authenticated user with no saved favourites → empty array."""
        conn, cur = mock_db
        cur.fetchall.return_value = []

        response = client.get("/api/v1/favourites", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "favourites" in data
        assert data["favourites"] == []

    def test_returns_saved_favourites(self, client, mock_db, auth_headers):
        """User with 2 favourited carparks → list includes both carpark IDs."""
        conn, cur = mock_db
        cur.fetchall.return_value = [
            {
                "carpark_id": "ACM",
                "address": "Blk 123 Test St",
                "car_lots": 400,
                "lat": 1.3521,
                "lng": 103.8198,
                "available_lots": 150,
                "vacancy_rate": 0.375,
                "weather_condition": "cloudy",
            },
            {
                "carpark_id": "A11",
                "address": "Blk 456 Main Rd",
                "car_lots": 300,
                "lat": 1.3000,
                "lng": 103.8500,
                "available_lots": 50,
                "vacancy_rate": 0.167,
                "weather_condition": "rainy",
            },
        ]

        response = client.get("/api/v1/favourites", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["favourites"]) == 2
        assert data["favourites"][0]["carpark_id"] == "ACM"
        assert data["favourites"][1]["carpark_id"] == "A11"
        # Verify each favourite has the expected fields
        for fav in data["favourites"]:
            assert "carpark_id" in fav
            assert "address" in fav
            assert "car_lots" in fav
            assert "available_lots" in fav
            assert "vacancy_rate" in fav


class TestAddFavourite:
    def test_requires_auth(self, client):
        """POST /favourites/ACM without auth token → 401."""
        response = client.post("/api/v1/favourites/ACM")
        assert response.status_code == 401

    def test_add_success(self, client, mock_db, auth_headers):
        """Add an existing carpark to favourites → 200."""
        conn, cur = mock_db
        # First query: check carpark exists → returns a row
        cur.fetchone.return_value = [1]

        response = client.post(
            "/api/v1/favourites/ACM", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_nonexistent_carpark_returns_404(self, client, mock_db, auth_headers):
        """Add a carpark that doesn't exist → 404."""
        conn, cur = mock_db
        # Carpark check returns None → not found
        cur.fetchone.return_value = None

        response = client.post(
            "/api/v1/favourites/FAKE999", headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestRemoveFavourite:
    def test_requires_auth(self, client):
        """DELETE /favourites/ACM without auth token → 401."""
        response = client.delete("/api/v1/favourites/ACM")
        assert response.status_code == 401

    def test_remove_success(self, client, mock_db, auth_headers):
        """Remove a favourited carpark → 200."""
        conn, cur = mock_db
        # DELETE query doesn't need fetchone/fetchall return values

        response = client.delete(
            "/api/v1/favourites/ACM", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_remove_nonexistent_is_idempotent(self, client, mock_db, auth_headers):
        """Removing a carpark not in favourites is still 200 (DELETE is idempotent)."""
        conn, cur = mock_db

        response = client.delete(
            "/api/v1/favourites/NOTSAVED", headers=auth_headers
        )

        # DELETE doesn't check if the row exists first — it just returns ok
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
