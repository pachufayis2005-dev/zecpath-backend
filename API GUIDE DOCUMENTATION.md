# Zecpath API — Developer Guide

Welcome! This guide will get you up and running with the Zecpath API — a job portal platform with candidate, employer, and admin roles, AI-powered resume scoring, and interview scheduling.

## Base URL

```
http://3.110.43.106/api/
```

## Interactive API Docs (Swagger)

Every endpoint is documented and testable live at:

```
http://3.110.43.106/api/docs/
```

You can browse all available endpoints, see example requests/responses, and even try them out directly from your browser using the **Authorize** button (see Authentication below).

---

## Authentication

Zecpath's API uses **JWT (JSON Web Tokens)** for authentication. You log in once, get a token, and attach that token to every request you make after that — instead of sending your username and password each time.

### 1. Getting a token

Send a `POST` request to `/api/login/` with your username and password:

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

If your credentials are correct, you'll get back two tokens:

```json
{
  "access": "eyJhbGciOi...",
  "refresh": "eyJhbGciOi..."
}
```

- **`access` token** — use this to authenticate your requests. It's short-lived (expires in 30 minutes), so treat it like a temporary pass.
- **`refresh` token** — use this to get a new access token once the old one expires, without logging in again. It lasts 1 day.

### 2. Using the token

For every request to a protected endpoint, add this header:

```
Authorization: Bearer <your_access_token>
```

For example, using `curl`:
```bash
curl -H "Authorization: Bearer eyJhbGciOi..." http://3.110.43.106/api/jobs/latest/
```

If you're testing in the Swagger docs, click the **Authorize** button at the top of the page, paste in `Bearer <your_access_token>`, and every request you try from there on will include it automatically.

### 3. Refreshing an expired token

Once your access token expires, you don't need to log in again — just send your refresh token to `/api/token/refresh/`:

```json
{
  "refresh": "eyJhbGciOi..."
}
```

You'll get a new `access` token back to keep using.

### A note on permissions

Being logged in isn't always enough — some endpoints are restricted to a specific role (candidate, employer, or admin). If you get a `403 Forbidden` response even while logged in, it usually means your account's role doesn't have access to that particular action — that's expected behavior, not a bug.

---

## Quick Start Example

Here's a full working flow: log in, then call a protected endpoint.

**Step 1 — Log in:**
```bash
curl -X POST http://3.110.43.106/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

**Step 2 — Copy the `access` token from the response, then call an endpoint:**
```bash
curl -X GET http://3.110.43.106/api/jobs/latest/ \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## Common Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/signup/` | POST | Create a new account |
| `/api/login/` | POST | Log in and get JWT tokens |
| `/api/logout/` | POST | Blacklist a refresh token (log out) |
| `/api/token/refresh/` | POST | Get a new access token |
| `/api/jobs/` | GET | List all active jobs (supports search/filter query params) |
| `/api/jobs/create/` | POST | Post a new job (employer only) |
| `/api/jobs/latest/` | GET | Get the 5 most recent active jobs |
| `/api/jobs/featured/` | GET | Get featured jobs |
| `/api/jobs/{id}/apply/` | POST | Apply to a job (candidate only) |
| `/api/resume/parse/` | POST | Upload and parse a resume against a job, with ATS scoring |
| `/api/candidate/profile/` | GET/PUT/DELETE | View, update, or deactivate your candidate profile |
| `/api/employer/profile/` | GET/PUT/DELETE | View, update, or deactivate your employer profile |
| `/api/applications/` | GET | View your application history (candidate) |
| `/api/saved-jobs/` | GET | View your saved jobs (candidate) |

*For the full list of endpoints, including admin, analytics, payments, and interview scheduling, see the [interactive Swagger docs](http://3.110.43.106/api/docs/).*

---

## Error Handling

Errors are returned as JSON with an `error` or `detail` key describing what went wrong.

**Common status codes:**

| Code | Meaning |
|---|---|
| `200` | Success |
| `201` | Created successfully |
| `400` | Bad request — check your request body for missing/invalid fields |
| `401` | Not authenticated — your token is missing, invalid, or expired |
| `403` | Authenticated, but you don't have permission for this action (wrong role, or not your resource) |
| `404` | The resource (job, application, etc.) doesn't exist |
| `502` | An external service (e.g. payment gateway) failed |

**Example error response:**
```json
{
  "error": "Job not found"
}
```

---

## Rate Limits

To keep the platform stable, some endpoints are rate-limited:

| Scope | Limit |
|---|---|
| General authenticated requests | 100/day per user |
| Login attempts | 5/minute |
| Premium/AI-powered endpoints (e.g. candidate ranking, reports) | 30/minute |

If you exceed a limit, you'll get a `429 Too Many Requests` response.
