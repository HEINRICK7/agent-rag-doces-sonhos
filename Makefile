VENV_BIN ?= .venv/bin
PYTHON ?= $(VENV_BIN)/python
PIP ?= $(VENV_BIN)/pip
RUFF ?= $(VENV_BIN)/ruff
MYPY ?= $(VENV_BIN)/mypy
COVERAGE ?= $(VENV_BIN)/coverage
UVICORN ?= $(VENV_BIN)/uvicorn

.PHONY: install test test-infrastructure lint format typecheck architecture coverage check run compose-up compose-down migrate

install:
	$(PIP) install -r requirements-dev.txt

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"

test-infrastructure:
	RUN_INFRASTRUCTURE_TESTS=1 $(PYTHON) -m unittest tests.integration.infrastructure.test_services

lint:
	$(RUFF) check .

format:
	$(RUFF) format .

typecheck:
	$(MYPY) app

architecture:
	$(PYTHON) scripts/check_architecture.py

coverage:
	$(COVERAGE) run -m unittest discover -s tests -p "test_*.py"
	$(COVERAGE) report -m

check: lint typecheck architecture test

run:
	$(UVICORN) app.main:app --reload

compose-up:
	docker-compose up --build

compose-down:
	docker-compose down

migrate:
	alembic upgrade head
