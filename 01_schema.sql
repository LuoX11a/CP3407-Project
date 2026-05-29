-- ============================================================
-- ParkGuideSG - Database Schema
-- PostgreSQL 15+
-- PostGIS can be added later: CREATE EXTENSION postgis;
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLE: carparks
-- Static information for each HDB carpark
-- Coordinates stored as WGS84 (EPSG:4326) lat/lng
-- ============================================================
CREATE TABLE carparks (
    carpark_id      VARCHAR(20) PRIMARY KEY,
    address         TEXT NOT NULL,
    car_lots        INTEGER NOT NULL,
    motorcycle_lots INTEGER DEFAULT 0,
    svy21_x         DOUBLE PRECISION NOT NULL,
    svy21_y         DOUBLE PRECISION NOT NULL,
    lat             DOUBLE PRECISION NOT NULL,
    lng             DOUBLE PRECISION NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_carparks_lat_lng ON carparks (lat, lng);

-- ============================================================
-- TABLE: weather_stations
-- NEA weather station metadata
-- ============================================================
CREATE TABLE weather_stations (
    station_id  VARCHAR(100) PRIMARY KEY,
    name        TEXT NOT NULL,
    lat         DOUBLE PRECISION NOT NULL,
    lng         DOUBLE PRECISION NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- TABLE: weather_records
-- Timestamped weather readings from each station
-- ============================================================
CREATE TABLE weather_records (
    id                BIGSERIAL PRIMARY KEY,
    station_id        VARCHAR(100) NOT NULL REFERENCES weather_stations(station_id),
    timestamp         TIMESTAMPTZ NOT NULL,
    temperature       NUMERIC(4,1),
    humidity          NUMERIC(4,1),
    rainfall          NUMERIC(6,2),
    weather_condition VARCHAR(20),  -- light rain | heavy rain | clear | overcast

    CONSTRAINT chk_weather_condition CHECK (
        weather_condition IN ('light rain', 'moderate rain', 'heavy rain', 'showers',
                              'thundery showers', 'clear', 'fair', 'fair and warm',
                              'cloudy', 'partly cloudy', 'overcast', 'windy', 'hazy')
    )
);

CREATE INDEX idx_weather_records_station_ts
    ON weather_records (station_id, timestamp DESC);

CREATE INDEX idx_weather_records_ts
    ON weather_records (timestamp DESC);

CREATE UNIQUE INDEX idx_weather_records_unique
    ON weather_records (station_id, timestamp);

-- ============================================================
-- TABLE: public_holidays
-- Singapore public holidays for temporal feature derivation
-- ============================================================
CREATE TABLE public_holidays (
    date DATE PRIMARY KEY,
    name TEXT NOT NULL
);

-- ============================================================
-- TABLE: availability_logs
-- Core time-series table — resampled to 15/30 minute intervals
-- ============================================================
CREATE TABLE availability_logs (
    id                  BIGSERIAL PRIMARY KEY,
    carpark_id          VARCHAR(20) NOT NULL REFERENCES carparks(carpark_id),
    timestamp           TIMESTAMPTZ NOT NULL,
    available_lots      INTEGER NOT NULL,
    vacancy_rate        NUMERIC(4,3) NOT NULL,
    weather_condition   VARCHAR(20),

    -- Derived temporal features for ML training
    hour                SMALLINT NOT NULL CHECK (hour BETWEEN 0 AND 23),
    day_of_week         SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    is_weekend          BOOLEAN NOT NULL,
    is_public_holiday   BOOLEAN NOT NULL DEFAULT FALSE,

    created_at          TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT chk_vacancy_rate CHECK (vacancy_rate >= 0 AND vacancy_rate <= 1),
    CONSTRAINT chk_available_lots CHECK (available_lots >= 0)
);

-- Primary lookup: get time-series for a specific carpark
CREATE INDEX idx_avail_carpark_ts
    ON availability_logs (carpark_id, timestamp DESC);

-- Range scan: pull training window (1–3 months)
CREATE INDEX idx_avail_ts
    ON availability_logs (timestamp DESC);

-- ML training filter by temporal features
CREATE INDEX idx_avail_features
    ON availability_logs (carpark_id, hour, day_of_week);

-- ============================================================
-- TABLE: ml_predictions
-- Cached prediction results for the live map
-- ============================================================
CREATE TABLE ml_predictions (
    id                      BIGSERIAL PRIMARY KEY,
    carpark_id              VARCHAR(20) NOT NULL REFERENCES carparks(carpark_id),
    prediction_time         TIMESTAMPTZ NOT NULL,
    forecast_timestamp      TIMESTAMPTZ NOT NULL,
    predicted_vacancy_rate  NUMERIC(4,3) NOT NULL,
    predicted_available_lots INTEGER NOT NULL,
    model_version           VARCHAR(20) NOT NULL DEFAULT 'v1',
    trend_series            NUMERIC(4,3)[],

    CONSTRAINT chk_pred_vacancy_rate CHECK (predicted_vacancy_rate >= 0 AND predicted_vacancy_rate <= 1)
);

CREATE INDEX idx_ml_carpark_forecast
    ON ml_predictions (carpark_id, forecast_timestamp DESC);

-- ============================================================
-- TABLE: ml_models
-- Track deployed model versions and training metadata
-- ============================================================
CREATE TABLE ml_models (
    model_version   VARCHAR(20) PRIMARY KEY,
    model_type      VARCHAR(20) NOT NULL,  -- LightGBM | XGBoost
    training_start  TIMESTAMPTZ NOT NULL,
    training_end    TIMESTAMPTZ NOT NULL,
    metrics         JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- FUNCTION: haversine_distance
-- Calculate distance in metres between two (lat, lng) points
-- ============================================================
CREATE OR REPLACE FUNCTION haversine_distance(
    lat1 DOUBLE PRECISION, lng1 DOUBLE PRECISION,
    lat2 DOUBLE PRECISION, lng2 DOUBLE PRECISION
) RETURNS DOUBLE PRECISION AS $$
DECLARE
    r     DOUBLE PRECISION := 6371000;  -- Earth radius in metres
    dlat  DOUBLE PRECISION;
    dlng  DOUBLE PRECISION;
    a     DOUBLE PRECISION;
    c     DOUBLE PRECISION;
BEGIN
    dlat := radians(lat2 - lat1);
    dlng := radians(lng2 - lng1);
    a    := sin(dlat / 2)^2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2)^2;
    c    := 2 * atan2(sqrt(a), sqrt(1 - a));
    RETURN r * c;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================
-- FUNCTION: find_nearest_station
-- Returns the station_id nearest to a given carpark
-- ============================================================
CREATE OR REPLACE FUNCTION find_nearest_station(
    cp_lat DOUBLE PRECISION,
    cp_lng DOUBLE PRECISION
) RETURNS VARCHAR(20) AS $$
    SELECT station_id
    FROM weather_stations
    ORDER BY haversine_distance(cp_lat, cp_lng, lat, lng)
    LIMIT 1;
$$ LANGUAGE sql STABLE;

-- ============================================================
-- VIEW: v_carpark_latest
-- Latest availability for each carpark (used by map markers)
-- ============================================================
CREATE OR REPLACE VIEW v_carpark_latest AS
SELECT DISTINCT ON (carpark_id)
    carpark_id,
    timestamp,
    available_lots,
    vacancy_rate,
    weather_condition
FROM availability_logs
ORDER BY carpark_id, timestamp DESC;

-- ============================================================
-- VIEW: v_carpark_map
-- Everything needed to render a map marker
-- ============================================================
CREATE OR REPLACE VIEW v_carpark_map AS
SELECT
    c.carpark_id,
    c.address,
    c.car_lots,
    c.lat,
    c.lng,
    l.available_lots,
    l.vacancy_rate,
    l.weather_condition,
    l.timestamp AS last_updated,
    CASE
        WHEN l.vacancy_rate > 0.5 THEN 'green'
        WHEN l.vacancy_rate > 0.2 THEN 'yellow'
        ELSE 'red'
    END AS marker_color
FROM carparks c
LEFT JOIN v_carpark_latest l ON c.carpark_id = l.carpark_id;
