#!/bin/bash
# clean_root_and_empty_dirs.sh
# Limpia la raíz y elimina carpetas vacías o innecesarias, dejando solo la estructura profesional

KEEP=("python" "docker" "docs" "tests" ".env" ".git" ".gitignore" "README.md" "clean_rifa_workspace.sh" "clean_enterprise_structure.sh")

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

# Eliminar subcarpetas vacías dentro de python, docs, tests
find python -type d -empty -delete 2>/dev/null
find docs -type d -empty -delete 2>/dev/null
find tests -type d -empty -delete 2>/dev/null

# Mensaje final
ls -la

echo "Limpieza de raíz y carpetas vacías completada."
