-- ============================================================
-- Migration: widen weather_condition columns
-- NEA 2-hour forecast API returns strings longer than 20 chars
-- (e.g. "Heavy Thundery Showers with Gusty Winds" = 43 chars)
-- Also drop the CHECK constraint — the API may add new values.
-- ============================================================

-- Drop dependent view first; it will be recreated below
DROP VIEW IF EXISTS v_carpark_latest CASCADE;

ALTER TABLE weather_records DROP CONSTRAINT IF EXISTS chk_weather_condition;

ALTER TABLE weather_records ALTER COLUMN weather_condition TYPE VARCHAR(50);
ALTER TABLE availability_logs ALTER COLUMN weather_condition TYPE VARCHAR(50);

CREATE VIEW v_carpark_latest AS
SELECT DISTINCT ON (carpark_id) carpark_id,
    "timestamp",
    available_lots,
    vacancy_rate,
    weather_condition
FROM availability_logs
ORDER BY carpark_id, "timestamp" DESC;
