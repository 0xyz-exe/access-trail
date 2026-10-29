# Access Certification and Review Workflow

## Overview

Access reviews allow security administrators, team leads, and resource owners to recertify or revoke permissions on a recurring cadence.

```
┌─────────────────────────────────┐
│  Create Certification Campaign  │
│  - Select Scope (Privileged)    │
│  - Set Reviewer & Due Date      │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Reviewer Certification Actions │
│  - Approve: Keep active grant   │
│  - Revoke:  Queue deprovision   │
│  - Escalate: Re-route to lead   │
└────────────────┬────────────────┘
                 │ (Verdict = Revoke)
                 ▼
┌─────────────────────────────────┐
│   Revocation State Machine      │
│   [Requested] ──► [Executing]   │
│        │               │        │
│        ▼               ▼        │
│    [Failed]       [Completed]   │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ Cryptographic Tamper-Evident    │
│ Audit Trail Recorded            │
└─────────────────────────────────┘
```

## Separation of Duties (Anti-Self-Approval)

A core compliance requirement is preventing reviewers from approving their own administrative privileges.

- In `backend/app/services/review_service.py`, `ReviewService.record_decision` validates that `identity.email != actor.email`.
- Any attempt to certify one's own access throws `HTTP 400 Separation of Duties violation: Reviewers cannot approve or certify their own access.`
