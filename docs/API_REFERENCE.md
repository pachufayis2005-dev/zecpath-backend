# Zecpath Backend — API Reference

This document gives a written overview of the Zecpath API, grouped by feature
area. For exact request/response schemas, try-it-out testing, and full field
details, use the **interactive Swagger docs** at `/api/docs/` (or Redoc at
`/api/redoc/`) on the running server — this document is a companion overview,
not a replacement.

**Base URL:** `http://zecpath-fayis.duckdns.org/api/`

---

## Authentication

Zecpath uses **JWT (JSON Web Token)** authentication via
`djangorestframework-simplejwt`.

| Endpoint | Purpose |
|---|---|
| `signup/` | Register a new Candidate or Employer account |
| `login/` | Obtain access + refresh JWT tokens |
| `token/refresh/` | Exchange a refresh token for a new access token |
| `logout/` | Blacklist the current refresh token |
| `auth-test/` | Verify a token is valid and see the authenticated user |

Once logged in, include the access token on all subsequent requests:

```
Authorization: Bearer <access_token>
```

Access tokens expire after 30 minutes; refresh tokens after 1 day (see
`SIMPLE_JWT` settings). Login is rate-limited to 5 attempts/minute per IP.

---

## Jobs

| Endpoint | Purpose |
|---|---|
| `jobs/` | List all active job postings (public) |
| `jobs/create/` | Employer creates a new job posting |
| `jobs/<id>/update/` | Employer updates a job posting |
| `jobs/<id>/status/` | Change a job's status (active/closed) |
| `jobs/<id>/remove/` | Admin removes a spam/flagged job |
| `jobs/featured/` | Get featured job listings |
| `jobs/latest/` | Get most recently posted jobs |
| `jobs/recommended/` | Get jobs recommended for the logged-in candidate |
| `jobs/<id>/apply/` | Candidate applies to a job |
| `jobs/<id>/save/` | Candidate saves a job for later |
| `saved-jobs/` | List a candidate's saved jobs |
| `jobs/<id>/applicants/` | Employer views applicants for a job |
| `jobs/<id>/analytics/` | Employer views application count for a job |
| `jobs/<id>/shortlist-ratio/` | Employer views shortlist ratio for a job |
| `jobs/<id>/ranked-candidates/` | Employer views candidates ranked by ATS score |

---

## Applications

| Endpoint | Purpose |
|---|---|
| `applications/` | Candidate's full application history |
| `applications/jobs/` | Jobs a candidate has applied to |
| `applications/<id>/status/` | Update an application's status |
| `applications/<id>/update-status/` | Employer updates application status (named route) |
| `applications/timeline/` | Timeline view of an application's progress |
| `applications/interview-status/` | Check interview status for an application |
| `applications/process/` | Batch-process pending applications (auto-shortlist) |
| `applications/<id>/report/` | Generate a candidate report for an application |

---

## Candidate & Employer Profiles

| Endpoint | Purpose |
|---|---|
| `candidate/profile/` | View/update the logged-in candidate's profile |
| `candidate/dashboard/` | Candidate's dashboard summary |
| `employer/profile/` | View/update the logged-in employer's profile |
| `employer/jobs/` | List jobs posted by the logged-in employer |
| `resume/parse/` | Upload and parse a resume (PDF/DOCX) for ATS scoring |

---

## AI Interview

| Endpoint | Purpose |
|---|---|
| `ai-answer/<answer_id>/submit/` | Submit a candidate's answer to an AI-generated question |
| `ai-answer/<id>/score/` | Get the AI-evaluated score for an answer |
| `availability/create/` | Employer creates an interview availability slot |
| `availability/` | List available interview slots |
| `interview/book/` | Candidate books an interview slot |
| `interviews/send-reminders/` | Trigger interview reminder emails (also runs via Celery beat) |

---

## Analytics

| Endpoint | Purpose |
|---|---|
| `analytics/funnel/` | Hiring funnel (applied → shortlisted → interviewed → hired) |
| `analytics/jobs/` | Per-job performance metrics |
| `analytics/conversion/` | Application-to-hire conversion ratio |
| `analytics/ai/` | AI interview usage/performance analytics |

---

## Payments & Billing

| Endpoint | Purpose |
|---|---|
| `payments/create-order/` | Create a Razorpay payment order |
| `payments/verify/` | Verify a completed payment's signature |
| `payments/capture/` | Capture an authorized payment |
| `payments/webhook/` | Razorpay webhook receiver (server-to-server, not user-facing) |
| `subscription/status/` | Check the logged-in user's subscription status |

Admin billing endpoints (require admin role):

| Endpoint | Purpose |
|---|---|
| `admin/billing/transactions/` | List all transactions |
| `admin/billing/transactions/<id>/refund/` | Issue a refund |
| `admin/billing/history/` | Full billing history |
| `admin/billing/revenue/daily/` | Daily revenue report |
| `admin/billing/revenue/monthly/` | Monthly revenue report |
| `admin/billing/revenue/plans/` | Revenue broken down by subscription plan |
| `admin/billing/revenue/summary/` | Overall revenue summary |

---

## Admin

| Endpoint | Purpose |
|---|---|
| `admin/test/` | Verify admin-level access |
| `admin/platform-stats/` | Overall platform statistics |
| `admin/job-activity/` | Recent job posting activity |
| `admin/audit-logs/` | System audit log |
| `employers/<id>/approve/` | Approve a pending employer account |
| `users/<id>/block/` | Block a user account |
| `users/test/` | Verify authenticated user access |

---

## API Documentation & Schema

| Endpoint | Purpose |
|---|---|
| `schema/` | Raw OpenAPI 3.0 schema (JSON) |
| `docs/` | Interactive Swagger UI |
| `redoc/` | Interactive Redoc UI (alternative style) |

---

## Permissions Summary

- Most endpoints require a valid JWT (`IsAuthenticated`)
- `jobs/` (list) is public (`AllowAny`)
- `admin/*` endpoints require an admin/staff account
- `employer/*` and job-creation endpoints require an Employer account
- `candidate/*` endpoints require a Candidate account

---

## Rate Limits

| Scope | Limit |
|---|---|
| General authenticated user | 100 requests/day |
| Login | 5 requests/minute |
| Premium API endpoints | 30 requests/minute |

**Known limitation:** the public `jobs/` list endpoint currently inherits the
general 100/day throttle even for anonymous users, since it has no
view-level throttle override. This was identified during QA testing and is
tracked as a follow-up fix (see QA Sign-Off Report).