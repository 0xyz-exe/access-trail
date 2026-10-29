.PHONY: install seed test build run

install:
	uv sync
	cd frontend && npm install

seed:
	uv run python -m backend.app.cli.main seed-demo

test:
	uv run pytest -v

build:
	cd frontend && npm run build

run:
	uv run python -m uvicorn backend.app.main:app --reload --port 8000
