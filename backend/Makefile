.PHONY: help dev test migrate superuser typecheck lint format clean install

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Run development server"
	@echo "  make test       - Run tests"
	@echo "  make migrate    - Run database migrations"
	@echo "  make superuser  - Create superuser"
	@echo "  make typecheck  - Run mypy type checking"
	@echo "  make lint       - Run ruff linter"
	@echo "  make format     - Format code with black"
	@echo "  make clean      - Clean up generated files"

install:
	uv add -e ".[dev]"

dev:
	uv run manage.py runserver

test:
	uv run pytest

migrate:
	uv run manage.py makemigrations
	uv run manage.py migrate

superuser:
	uv run manage.py createsuperuser

typecheck:
	uv run mypy .

lint:
	uv run ruff check .

format:
	uv run black .
	uv run ruff check --fix .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
