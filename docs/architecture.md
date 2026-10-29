# AccessTrail Architecture

## 1. System Overview

AccessTrail is a centralized identity inventory, entitlement governance, access certification, and cryptographic audit platform designed according to Zero Trust principles.

```
┌────────────────────────────────────────────────────────┐
│                   Web Console (React / Vite)            │
│  - Dashboard & Risk Radar   - Identity Inventory       │
│  - Certification Workbench  - Revocation Center        │
│  - Tamper-Evident Explorer  - Evidence Exporter        │
└──────────────────────────┬─────────────────────────────┘
                           │ REST API (/api/v1)
┌──────────────────────────▼─────────────────────────────┐
│                   FastAPI Application Core             │
│  ┌──────────────────────┐   ┌────────────────────────┐ │
│  │  Authentication &    │   │  Deterministic Risk    │ │
│  │  Tenant Isolation    │   │  Engine                │ │
│  └──────────────────────┘   └────────────────────────┘ │
│  ┌──────────────────────┐   ┌────────────────────────┐ │
│  │  Access Review &     │   │  Revocation State      │ │
│  │  SoD Policy Engine   │   │  Machine & Connectors  │ │
│  └──────────────────────┘   └────────────────────────┘ │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Tamper-Evident SHA-256 Audit Hash Chain         │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────┬─────────────────────────────┘
                           │ SQLAlchemy 2.x
┌──────────────────────────▼─────────────────────────────┐
│        Relational Storage (SQLite Dev / PostgreSQL)    │
│  - organizations    - identities      - entitlements   │
│  - access_grants    - review_campaigns- audit_events   │
└────────────────────────────────────────────────────────┘
```

## 2. Multi-Tenancy & Data Isolation

- Every security entity inherits from `TenantScopedMixin`, ensuring `tenant_id` tagging.
- Backend dependencies resolve `current_user` from active session token and enforce tenant boundary on all SQL queries.
- Cross-tenant data leaks and unauthorized IDOR queries are strictly rejected at the service layer.

## 3. Cryptographic Tamper-Evident Audit Trail

Every audit event is cryptographically hashed:
$$\text{EventHash}_i = \text{SHA256}(\text{EventHash}_{i-1} \parallel \text{CanonicalJSON}(P_i))$$
- Genesis event references 64 zeroes.
- Canonical JSON sorts keys deterministically and strips superfluous whitespace.
- `/api/v1/audit-logs/verify` traverses the chain and pinpoints any corrupted or deleted events.
