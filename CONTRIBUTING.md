# Contributing to AccessTrail

Thank you for contributing to AccessTrail!

## Development Setup

1. Clone the repository
2. Install Python dependencies: `uv sync`
3. Install frontend dependencies: `cd frontend && npm install`
4. Seed demo data: `uv run python -m backend.app.cli.main seed-demo`
5. Run tests: `uv run pytest`
6. Build frontend: `cd frontend && npm run build`

## Pull Request Guidelines

- Ensure `uv run pytest` passes 100%.
- Ensure `cd frontend && npm run build` passes with 0 type errors.
- Sign your commits.
