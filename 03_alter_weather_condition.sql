-- ============================================================
-- Migration: widen weather_condition columns
-- NEA 2-hour forecast API returns strings longer than 20 chars
-- (e.g. "Heavy Thundery Showers with Gusty Winds" = 43 chars)
-- Also drop the CHECK constraint — the API may add new values.
-- ============================================================

ALTER TABLE weather_records DROP CONSTRAINT IF EXISTS chk_weather_condition;

ALTER TABLE weather_records ALTER COLUMN weather_condition TYPE VARCHAR(50);
ALTER TABLE availability_logs ALTER COLUMN weather_condition TYPE VARCHAR(50);
