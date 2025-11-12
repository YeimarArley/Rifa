#!/bin/bash
# clean_rifa_workspace.sh - Limpia archivos/carpetas fuera de la estructura profesional (solo deja python/ y .env)
# Uso: bash clean_rifa_workspace.sh

ROOT_DIR="$(dirname "$0")"
cd "$ROOT_DIR"

# Lista blanca
KEEP=("python" ".env" ".git" ".gitignore" "README.md")

for item in * .*; do
  skip=false
  for keep in "${KEEP[@]}"; do
    if [[ "$item" == "$keep" ]]; then
      skip=true
      break
    fi
  done
  if [[ "$skip" == false && "$item" != "." && "$item" != ".." ]]; then
    echo "Eliminando: $item"
    rm -rf "$item"
  fi
done

echo "Limpieza completada. Solo quedan: ${KEEP[*]}"
