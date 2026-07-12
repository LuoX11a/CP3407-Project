"""Tests for recommendation logic — status and trend functions."""

from app.routers.recommend import _status, _make_trend
from app.models.schemas import CarparkResult, RecommendResponse, TrendPoint


class TestStatus:
    def test_green_above_50_percent(self):
        assert _status(0.51) == "GREEN"
        assert _status(0.75) == "GREEN"
        assert _status(1.0) == "GREEN"

    def test_yellow_between_20_and_50(self):
        assert _status(0.21) == "YELLOW"
        assert _status(0.5) == "YELLOW"
        assert _status(0.35) == "YELLOW"

    def test_red_below_20(self):
        assert _status(0.0) == "RED"
        assert _status(0.1) == "RED"
        assert _status(0.2) == "RED"

    def test_boundary_values(self):
        assert _status(0.501) == "GREEN"
        assert _status(0.201) == "YELLOW"


class TestTrend:
    def test_trend_returns_3_points(self):
        trend = _make_trend(hour_now=14, predicted=0.5)
        assert len(trend) == 3

    def test_trend_hours_wrap_around(self):
        trend = _make_trend(hour_now=23, predicted=0.5)
        assert trend[0].hour == "00:00"
        assert trend[1].hour == "01:00"
        assert trend[2].hour == "02:00"

    def test_trend_rates_in_valid_range(self):
        trend = _make_trend(hour_now=10, predicted=0.3)
        for point in trend:
            assert 0.0 <= point.rate <= 1.0

    def test_trend_with_high_vacancy(self):
        trend = _make_trend(hour_now=10, predicted=0.9)
        for point in trend:
            assert 0.0 <= point.rate <= 1.0


class TestSchemas:
    def test_carpark_result_validation(self):
        cp = CarparkResult(
            carpark_id="ACM",
            address="123 Test St",
            total_lots=400,
            available_lots=150,
            predicted_vacancy_rate=0.375,
            status="YELLOW",
            distance_m=230.0,
            weather="Cloudy",
            lat=1.3521,
            lng=103.8198,
            trend=[TrendPoint(hour="15:00", rate=0.38)],
        )
        assert cp.carpark_id == "ACM"
        assert cp.status == "YELLOW"

    def test_recommend_response_validation(self):
        resp = RecommendResponse(
            results=[],
            query_time_ms=12.5,
        )
        assert resp.results == []
        assert resp.query_time_ms == 12.5
