# Database Schema

AccessTrail utilizes a normalized relational schema with foreign key constraints, indexes, and tenant-scoped isolation.

## Primary Entities

### 1. `organizations`
- `id` (PK, string)
- `name` (string, unique)
- `slug` (string, unique)
- `description` (text)
- `is_active` (boolean)

### 2. `users`
- `id` (PK, string)
- `tenant_id` (FK, indexed)
- `email` (string, indexed)
- `full_name` (string)
- `password_hash` (PBKDF2-HMAC-SHA256)
- `role` (platform_owner, security_admin, access_reviewer, auditor, read_only_analyst, standard_user)
- `session_token` (indexed)
- `is_active` (boolean)

### 3. `identities`
- `id` (PK, string)
- `tenant_id` (FK, indexed)
- `username` (string, indexed)
- `email` (string, nullable)
- `full_name` (string)
- `identity_type` (human, admin, service_account, app, contractor)
- `status` (active, inactive, suspended)
- `department` (string, nullable)
- `manager_email` (string, nullable)
- `source_system` (local, okta, azure_ad, google_workspace, csv)
- `is_privileged` (boolean)
- `risk_score` (integer, 0-100)

### 4. `applications` & `entitlements`
- `applications`: `name`, `app_type`, `is_sensitive`
- `entitlements`: `application_id`, `permission_name`, `permission_type`, `risk_level`

### 5. `access_grants`
- `id` (PK, string)
- `tenant_id` (FK, indexed)
- `identity_id` (FK to identities)
- `application_id` (FK to applications)
- `entitlement_id` (FK to entitlements)
- `is_direct` (boolean - direct grant vs inherited role)
- `granted_by` (string)
- `grant_date` (datetime)
- `business_justification` (text)
- `expires_at` (datetime, nullable)
- `status` (active, revoked, expired)

### 6. `review_campaigns` & `review_decisions`
- `review_campaigns`: `name`, `scope`, `reviewer_id`, `status`, `start_date`, `due_date`, `total_items`, `reviewed_items`
- `review_decisions`: `campaign_id`, `reviewer_id`, `identity_id`, `grant_id`, `decision` (approve, revoke, request_info, escalate), `comments`, `decided_at`

### 7. `revocation_requests`
- `id` (PK, string)
- `decision_id` (FK to review_decisions)
- `grant_id` (FK to access_grants)
- `identity_id` (FK to identities)
- `status` (requested, pending_approval, approved, executing, completed, failed, cancelled)
- `target_system` (string)
- `error_message` (text)
- `retry_count` (integer)
- `executed_at` (datetime)

### 8. `risk_findings`
- `tenant_id`, `identity_id`, `finding_type`, `severity` (low, medium, high, critical), `rule_name`, `evidence`, `remediation`, `status`

### 9. `audit_events`
- `tenant_id`, `timestamp`, `actor_id`, `actor_name`, `action`, `target_entity`, `category`, `result`, `metadata_json`, `prev_hash`, `event_hash`
