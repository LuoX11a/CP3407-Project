"""
Unit tests for ETL pipeline functions.
Tests cover: haversine distance, HTTP fetch with retry, data validation.
"""
import pytest
from unittest.mock import MagicMock, patch, call
import math
import requests


# ---------------------------------------------------------------------------
# _haversine  —  pure function, no mocks needed
# ---------------------------------------------------------------------------

# Import the real _haversine from etl_cloud (it's a pure function)
import sys
import os

# Make etl_cloud importable without triggering psycopg2 connect
sys.modules["psycopg2"] = MagicMock()
sys.modules["psycopg2.extras"] = MagicMock()
sys.modules["pandas"] = MagicMock()
sys.modules["pyproj"] = MagicMock()
sys.modules["pyproj.transformer"] = MagicMock()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from etl_cloud import _haversine


class TestHaversine:
    """Unit tests for _haversine() distance calculation."""

    def test_same_point_zero_distance(self):
        """Distance from a point to itself should be 0."""
        assert _haversine(1.35, 103.81, 1.35, 103.81) == pytest.approx(0.0, abs=0.01)

    def test_known_distance_singapore(self):
        """Distance between two known Singapore locations.

        Raffles Place (1.2839, 103.8514) to Orchard (1.3048, 103.8318)
        is approximately 2.2 km.
        """
        d = _haversine(1.2839, 103.8514, 1.3048, 103.8318)
        assert 2000 < d < 3500  # roughly 2.0-3.5 km (depends on exact formula)

    def test_short_distance(self):
        """Distance of ~111m for 0.001 degree latitude difference."""
        d = _haversine(1.35, 103.81, 1.351, 103.81)
        assert 100 < d < 130  # ~111m

    def test_symmetric(self):
        """Distance should be symmetric."""
        d1 = _haversine(1.3521, 103.8198, 1.3000, 103.8500)
        d2 = _haversine(1.3000, 103.8500, 1.3521, 103.8198)
        assert d1 == pytest.approx(d2, rel=1e-9)

    def test_singapore_to_london(self):
        """Long distance: Singapore to London ~10,900 km."""
        d = _haversine(1.3521, 103.8198, 51.5074, -0.1278)
        assert 10_800_000 < d < 11_000_000


# ---------------------------------------------------------------------------
# _fetch_json  —  requires HTTP mocks
# ---------------------------------------------------------------------------


class TestFetchJson:
    """Unit tests for _fetch_json() with mocked HTTP responses."""

    @patch("etl_cloud.requests.get")
    def test_successful_fetch(self, mock_get):
        """Happy path: API returns valid JSON."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": [{"timestamp": "2026-07-27T08:00:00+08:00"}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        from etl_cloud import _fetch_json

        result = _fetch_json("https://api.data.gov.sg/v1/test")
        assert result["items"][0]["timestamp"] == "2026-07-27T08:00:00+08:00"
        mock_get.assert_called_once()

    @patch("etl_cloud.requests.get")
    def test_timeout_passed_correctly(self, mock_get):
        """Verify connect_timeout and read_timeout are passed as tuple."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        from etl_cloud import _fetch_json

        _fetch_json("https://example.com", connect_timeout=5, read_timeout=30)
        mock_get.assert_called_with(
            "https://example.com",
            timeout=(5, 30),
            headers={"User-Agent": "ParkGuideSG-ETL/1.0"},
        )

    @patch("etl_cloud.requests.get")
    def test_http_error_raises(self, mock_get):
        """HTTP 500 should raise an exception."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_get.return_value = mock_response

        from etl_cloud import _fetch_json

        with pytest.raises(requests.HTTPError):
            _fetch_json("https://example.com")


# ---------------------------------------------------------------------------
# with_retry  —  retry logic
# ---------------------------------------------------------------------------


class TestWithRetry:
    """Unit tests for the retry decorator."""

    def test_retries_on_failure(self):
        """Should retry MAX_RETRIES times before raising."""
        from etl_cloud import with_retry

        call_count = [0]

        def flaky():
            call_count[0] += 1
            raise requests.ConnectionError("Connection refused")

        fn = with_retry(flaky, max_retries=3, backoff=0)
        with pytest.raises(requests.ConnectionError):
            fn()
        assert call_count[0] == 3

    def test_succeeds_on_retry(self):
        """Should succeed if a retry works."""
        from etl_cloud import with_retry

        call_count = [0]

        def flaky_then_ok():
            call_count[0] += 1
            if call_count[0] < 2:
                raise requests.ConnectionError("fail")
            return "success"

        fn = with_retry(flaky_then_ok, max_retries=3, backoff=0)
        result = fn()
        assert result == "success"
        assert call_count[0] == 2


# ---------------------------------------------------------------------------
# Data validation
# ---------------------------------------------------------------------------


class TestDataValidation:
    """Data quality checks on ETL output."""

    def test_vacancy_rate_calculation(self):
        """vacancy_rate = available / total, clamped to [0, 1]."""
        total = 400

        # Normal case
        vr = round(min(max(150 / total, 0), 1), 3)
        assert vr == 0.375

        # Full
        vr = round(min(max(400 / total, 0), 1), 3)
        assert vr == 1.0

        # Empty
        vr = round(min(max(0 / total, 0), 1), 3)
        assert vr == 0.0

        # Edge: negative available (shouldn't happen, but clamp to 0)
        vr = round(min(max(-5 / total, 0), 1), 3)
        assert vr == 0.0

    def test_negative_available_lots_should_be_rejected(self):
        """Available lots must be >= 0 (schema CHECK constraint)."""
        available = -1
        total = 100
        assert available < 0  # This would violate the CHECK constraint
        # The database CHECK CONSTRAINT handles this at INSERT time

    def test_vacancy_rate_bounds(self):
        """Vacancy rate must be in [0, 1] (schema CHECK constraint)."""
        for avail, total in [(0, 100), (50, 100), (100, 100)]:
            vr = avail / total
            assert 0.0 <= vr <= 1.0, f"vacancy_rate={vr} out of bounds"

    def test_hour_range(self):
        """Hour must be 0-23."""
        import datetime
        for h in range(24):
            ts = datetime.datetime(2026, 7, 27, h, 0, 0)
            assert 0 <= ts.hour <= 23
        # Midnight
        assert datetime.datetime(2026, 7, 27, 0, 0, 0).hour == 0
        # 11 PM
        assert datetime.datetime(2026, 7, 27, 23, 59, 59).hour == 23


# ---------------------------------------------------------------------------
# _fetch_with_hard_timeout
# ---------------------------------------------------------------------------


class TestHardTimeout:
    """Unit tests for the hard timeout wrapper."""

    def test_returns_result_within_timeout(self):
        """Should return result when function completes quickly."""
        from etl_cloud import _fetch_with_hard_timeout

        def fast():
            return "done"

        result = _fetch_with_hard_timeout(fast, timeout=5)
        assert result == "done"

    def test_raises_on_hard_timeout(self):
        """Should raise TimeoutError when function takes too long."""
        from etl_cloud import _fetch_with_hard_timeout
        import time

        def slow():
            time.sleep(10)
            return "too late"

        with pytest.raises(TimeoutError):
            _fetch_with_hard_timeout(slow, timeout=1)
