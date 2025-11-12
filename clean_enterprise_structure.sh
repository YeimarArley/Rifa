#!/bin/bash
# clean_enterprise_structure.sh
# Deja solo la estructura profesional recomendada para tu proyecto de rifa

KEEP=("python" "docker" "docs" "tests" ".env" ".git" ".gitignore" "README.md" "clean_rifa_workspace.sh")

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
