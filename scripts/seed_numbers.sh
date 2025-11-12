#!/usr/bin/env bash
set -euo pipefail

# Inserta números del 1 al 2000 en la tabla assigned_numbers como disponibles
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-rifa_db}
DB_USER=${DB_USER:-rifa_user}

echo "Seed: insertando números 1..2000 en assigned_numbers (si no existen)"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 <<'SQL'
BEGIN;
CREATE TEMP TABLE tmp_nums(num int);
INSERT INTO tmp_nums SELECT generate_series(1,2000);
INSERT INTO assigned_numbers (number, status)
SELECT num, 'available' FROM tmp_nums
ON CONFLICT (number) DO NOTHING;
DROP TABLE tmp_nums;
COMMIT;
SQL

echo "Seed completado."
