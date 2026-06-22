-- ============================================================
-- ParkGuideSG - Users & Favourites
-- ============================================================

CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(50) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE favourites (
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    carpark_id  VARCHAR(20) NOT NULL REFERENCES carparks(carpark_id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id, carpark_id)
);
