# Deployment and Operations Guide

## 1. Quickstart with Docker Compose

AccessTrail provides a production-ready containerized environment:

```bash
docker compose up -d --build
```

Access the web console at `http://localhost:8000` (FastAPI serves both API and optimized React frontend build).

## 2. Seed Initial Demonstration Data

```bash
uv run python -m backend.app.cli.main seed-demo
```

### Preconfigured Test Users:
- **Platform Owner**: `admin@acme.corp` / `Password123!`
- **Security Admin**: `secadmin@acme.corp` / `Password123!`
- **Access Reviewer**: `reviewer@acme.corp` / `Password123!`
- **External Auditor**: `auditor@acme.corp` / `Password123!`
- **SOC Analyst**: `analyst@acme.corp` / `Password123!`

## 3. Cryptographic Audit Chain Verification

To verify the audit log integrity directly from the CLI:

```bash
uv run python -m backend.app.cli.main verify-audit
```

## 4. Environment Variables

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite:///./data/accesstrail.db` | Primary DB connection string (PostgreSQL or SQLite) |
| `SECRET_KEY` | *(Random 32-char dev key)* | Secret key for signing sessions and audit verification |
| `ENVIRONMENT` | `development` | Deployment environment flag |
| `PORT` | `8000` | Port for web server |
