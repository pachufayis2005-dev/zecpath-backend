# Zecpath Backend — Security Audit

This document reviews the security controls actually implemented in Zecpath,
and records findings from that review — including one issue that needs
fixing.

---

## 1. Authentication & Authorization

- **JWT-based auth** via `djangorestframework-simplejwt`. Access tokens
  expire after 30 minutes; refresh tokens after 1 day, with rotation and
  blacklisting enabled (`ROTATE_REFRESH_TOKENS`, `BLACKLIST_AFTER_ROTATION`)
  — a stolen refresh token can't be reused indefinitely.
- **Role-based permissions**: Candidate, Employer, and Admin roles enforced
  via `DEFAULT_PERMISSION_CLASSES` (`IsAuthenticated` by default) plus
  custom role-checking permissions on individual views.
- **Rate limiting** (`core/throttles.py` + DRF settings):
  - General authenticated users: 100 requests/day
  - Login attempts: 5/minute per IP (`LoginRateThrottle`, prevents
    brute-force credential guessing)
  - Premium API endpoints: 30/minute (`PremiumAPIRateThrottle`)

---

## 2. Audit Logging

Three separate logging mechanisms cover different concerns:

- **`core/security.py` (`log_unauthorized_access`)** — records unauthorized
  access attempts (IP address, user if authenticated, action) into
  `SecurityLog`.
- **`core/services/audit_service.py` (`AuditService`)** — records important
  user actions into `AuditTrail` (who did what, to which object).
- **`core/services/financial_security_service.py`
  (`FinancialSecurityService`)** — automatically flags any transaction of
  ₹100,000 or more as suspicious and logs it to `FinancialAuditLog` for
  review.

---

## 3. Payment Security

- Razorpay order creation happens server-side only (client never sees API
  secrets).
- Payment verification uses **HMAC signature verification computed
  locally** — the signature Razorpay returns is checked against a signature
  we compute ourselves, so a forged "payment succeeded" request without a
  valid signature is rejected. Verified in testing with both valid and
  invalid signatures.
- Suspicious/large transactions are automatically flagged (see above).

---

## 4. Data Protection

- Resumes are stored in a **private S3 bucket** (not publicly readable),
  accessed only via time-limited presigned URLs (1 hour expiry).
- `.env` (containing `SECRET_KEY`, database credentials, AWS keys, Razorpay
  keys) is excluded from Git via `.gitignore` — confirmed via
  `git log --all --full-history -- .env` showing no commits ever touched
  it.
- `EncryptionService` (`core/services/encryption_service.py`) provides
  Fernet-based symmetric encryption/decryption for sensitive text fields.

### ⚠️ Finding: Encryption key is not persisted

`EncryptionService` generates its encryption key at import time and never
loads it from environment configuration:

```python
KEY = Fernet.generate_key()
cipher = Fernet(KEY)
```

This means a **new random key is generated every time the application
process starts** (every deploy, every Gunicorn restart). Any data encrypted
with the previous key becomes **permanently undecryptable** after a
restart, since the key that encrypted it no longer exists anywhere.

**Fix required:** generate the key once, store it in `.env` as
`ENCRYPTION_KEY`, and load it via `os.getenv("ENCRYPTION_KEY")` instead of
calling `Fernet.generate_key()` in code. This is not yet fixed — flagged
here for the next iteration.

---

## 5. Network & Transport Security

- `ALLOWED_HOSTS` restricts which Host headers Django accepts — confirmed
  working in production (a malformed request with `Host: 0.0.0.0` was
  correctly rejected with `DisallowedHost`, visible in
  `logs/django_errors.log`).
- Security headers enabled: `SECURE_BROWSER_XSS_FILTER`,
  `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS = DENY` (prevents
  clickjacking via iframe embedding).
- Nginx dotfile access blocking configured (prevents accidental exposure of
  `.env`, `.git`, etc. if misconfigured).

**Note:** `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` are currently
`False`. This is acceptable only because the site is served over plain HTTP
(no SSL/TLS certificate configured yet on the DuckDNS domain). If/when HTTPS
is added, both should be switched to `True`.

---

## 6. Known Limitation (Carried from QA Testing)

The public `jobs/` list endpoint (`AllowAny`) still inherits the global
100/day `UserRateThrottle` for anonymous users, since it has no view-level
throttle override. Legitimate anonymous browsing could be blocked after
~100 requests/day from the same IP. Identified during QA load testing;
tracked as a follow-up fix, not yet resolved in code.

---

## 7. Summary of Findings

| Finding | Severity | Status |
|---|---|---|
| Encryption key regenerated on every restart | High (data loss on restart) | Open |
| Public `jobs/` endpoint inherits per-day throttle meant for authenticated use | Low | Open |
| No HTTPS/SSL on current deployment | Medium | Open (no cost-free cert configured yet) |
| Secrets never committed to Git | — | Verified clean |
| Payment signatures verified locally (not trusted blindly) | — | Verified working |