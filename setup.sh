#!/usr/bin/env bash
# ============================================================
# ParkGuideSG - One-shot database setup
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DB_NAME="${PG_DB:-parkguidesg}"
DB_USER="${PG_USER:-postgres}"

echo "=== ParkGuideSG Database Setup ==="
echo ""

# 1. Create the database (if it does not exist)
echo "[1/3] Creating database '${DB_NAME}'..."
psql -U "${DB_USER}" -tc \
    "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" \
    | grep -q 1 \
    || createdb -U "${DB_USER}" "${DB_NAME}"

# 2. Run schema
echo "[2/3] Applying schema..."
psql -U "${DB_USER}" -d "${DB_NAME}" -f "${SCRIPT_DIR}/01_schema.sql"

# 3. Seed public holidays
echo "[3/3] Seeding public holidays..."
psql -U "${DB_USER}" -d "${DB_NAME}" -f "${SCRIPT_DIR}/02_seed_holidays.sql"

echo ""
echo "=== Setup complete ==="
echo "Tables created:"
psql -U "${DB_USER}" -d "${DB_NAME}" -c "\dt"
