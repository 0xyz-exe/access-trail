# AccessTrail Threat Model

## 1. Threat Vectors and Controls

| Threat Category | Potential Impact | AccessTrail Architectural Mitigations |
| :--- | :--- | :--- |
| **Privilege Escalation** | Attacker assigns admin permissions or elevates role | Deny-by-default server-side RBAC dependencies (`require_role`), strictly isolating platform_owner/security_admin capabilities. |
| **Cross-Tenant Data Leakage** | Tenant A inspects or mutates Tenant B entities | Explicit `TenantScopedMixin` and tenant ID filtering injected into every DB query. Session token bound to tenant. |
| **Separation of Duties Bypass** | Reviewer approves own privileged access | Hard check in `ReviewService.record_decision`: if reviewer identity matches grant identity, HTTP 400 rejection is returned. |
| **Audit Log Tampering** | Malicious actor modifies historical audit logs | SHA-256 cryptographic hash chaining with canonical JSON representation. `/api/v1/audit-logs/verify` immediately flags altered records. |
| **Formula Injection (CSV)** | Malicious payload in export executes in Excel | `sanitize_csv_cell` escapes characters `=, +, -, @, \t, \r` with single-quote prefix. |
| **Credential & Secret Leakage** | Plaintext credentials exposed in logs or DB | Passwords hashed using PBKDF2-HMAC-SHA256 (600,000 iterations). Session tokens generated using 32-byte CSPRNG. |
| **Revocation Replay / Race** | Concurrent double-revocation causes external errors | Idempotent revocation state machine with transition locks and retry limits. |
