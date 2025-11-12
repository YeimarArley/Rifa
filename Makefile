PYTHON ?= python3
VENV = .venv
ACTIVATE = source $(VENV)/bin/activate

.PHONY: help setup init-db seed run test

help:
	@echo "Comandos disponibles:"
	@echo "  make setup      -> crear venv e instalar dependencias"
	@echo "  make init-db    -> inicializar Postgres y aplicar migración (usa scripts/init_db.sh)"
	@echo "  make seed       -> seedear números (1..2000) into assigned_numbers"
	@echo "  make run        -> ejecutar servidor (dev)"
	@echo "  make test       -> ejecutar tests unitarios"

setup:
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && pip install --upgrade pip
	$(ACTIVATE) && pip install -r requirements.txt

init-db:
	./scripts/init_db.sh

seed:
	./scripts/seed_numbers.sh

run:
	$(ACTIVATE) && $(PYTHON) server.py

test:
	$(ACTIVATE) && $(PYTHON) -m unittest discover -v tests
