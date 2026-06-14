"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from pydantic import BaseModel, Field


# ── Request ──────────────────────────────────────────────

class RecommendRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="User latitude (WGS84)")
    lng: float = Field(..., ge=-180, le=180, description="User longitude (WGS84)")
    n: int = Field(default=5, ge=1, le=10, description="Number of results")
    radius_m: int = Field(default=1000, ge=100, le=5000, description="Search radius in metres")


# ── Response items ───────────────────────────────────────

class TrendPoint(BaseModel):
    hour: str = Field(..., description="Hour label, e.g. '14:00'")
    rate: float = Field(..., description="Predicted vacancy rate at that hour")


class CarparkResult(BaseModel):
    carpark_id: str
    address: str
    total_lots: int
    available_lots: int
    predicted_vacancy_rate: float
    status: str  # GREEN / YELLOW / RED
    distance_m: float
    weather: str
    lat: float
    lng: float
    trend: list[TrendPoint]


class RecommendResponse(BaseModel):
    results: list[CarparkResult]
    query_time_ms: float
    attribution: str = "Data sourced from Data.gov.sg and NEA"


# ── Carpark detail ──────────────────────────────────────

class CarparkDetail(BaseModel):
    carpark_id: str
    address: str
    car_lots: int
    motorcycle_lots: int
    lat: float
    lng: float
    latest_available: int | None
    latest_vacancy: float | None
    latest_weather: str | None
    latest_updated: str | None


class HistoryPoint(BaseModel):
    timestamp: str
    available_lots: int
    vacancy_rate: float
    weather_condition: str | None


class CarparkHistoryResponse(BaseModel):
    carpark: CarparkDetail
    history: list[HistoryPoint]


# ── Health ───────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    db_connected: bool
    model_loaded: bool
    carpark_count: int
    latest_data_ts: str | None


# ── Auth ──────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    user_id: int
    username: str
    token: str


# ── Favourites ────────────────────────────────────────────

class FavouriteItem(BaseModel):
    carpark_id: str
    address: str
    car_lots: int
    lat: float
    lng: float
    available_lots: int
    vacancy_rate: float
    weather_condition: str | None


class FavouriteListResponse(BaseModel):
    favourites: list[FavouriteItem]


# ── Search ────────────────────────────────────────────────

class SearchResult(BaseModel):
    carpark_id: str
    address: str
    car_lots: int
    lat: float
    lng: float
    available_lots: int | None
    vacancy_rate: float | None


class SearchResponse(BaseModel):
    results: list[SearchResult]
