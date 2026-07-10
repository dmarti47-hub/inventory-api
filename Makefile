.PHONY: run test test-cov lint format db-up db-down docker-up docker-down docker-logs

run:
	uv run uvicorn app.main:app --reload --port 8001

test:
	uv run pytest -v

test-cov:
	uv run pytest --cov=app --cov-report=term-missing

lint:
	uv run ruff check .

format:
	uv run ruff format .

db-up:
	docker compose up -d db test_db

db-down:
	docker compose down

docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f api