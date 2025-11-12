#!/usr/bin/env bash
set -euo pipefail

# Inicializa la base de datos PostgreSQL para el proyecto Rifa.
# Usa las variables de entorno: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
# Si el usuario/BD no existen, los crea, y aplica migracion_postgresql.sql

DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-rifa_db}
DB_USER=${DB_USER:-rifa_user}
DB_PASSWORD=${DB_PASSWORD:-rifa_password}

export PGPASSWORD=${PGPASSWORD:-${DB_PASSWORD}}

echo "Esperando a que Postgres esté disponible en ${DB_HOST}:${DB_PORT}..."
# Espera hasta 60s
for i in {1..60}; do
  if pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; then
    echo "Postgres disponible"
    break
  fi
  sleep 1
done

echo "Creando usuario y base de datos si no existen..."
# Crear usuario (si no existe)
psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -tc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1 || \
  psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"

# Crear base de datos (si no existe)
psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 || \
  psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

echo "Aplicando migración: migracion_postgresql.sql"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f migracion_postgresql.sql

echo "Inicialización completada."
