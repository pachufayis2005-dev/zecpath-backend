# Day 13 Bug Report

## Security Testing

### Test Case 1: Unauthorized Access

Endpoint:
GET /api/candidate/profile/

Action:
Attempted to access protected endpoint without JWT token.

Expected:
Access should be denied.

Actual:
403 Forbidden returned.

Response:
```json
{
    "detail": "Authentication credentials were not provided."
}
```

Status:
PASS

## Test Case 2: Candidate Accessing Admin API

Endpoint:
GET /api/admin/test/

Action:
Candidate user attempted to access admin-only API.

Expected Result:
Access denied.

Actual Result:
403 Forbidden returned.

Response:
{
    "detail": "You do not have permission to perform this action."
}

Status:
PASS

## Status Code Testing

### 200 OK
Endpoint:
GET /api/candidate/profile/

Status:
PASS

---

### 201 Created
Endpoint:
POST /api/signup/

Status:
PASS

---

### 400 Bad Request
Endpoint:
POST /api/signup/

Cause:
Invalid role value.

Status:
PASS

---

### 403 Forbidden
Endpoint:
GET /api/admin/test/

Cause:
Role violation.

Status:
PASS

### Invalid Token Test

Endpoint:
GET /api/candidate/profile/

Action:
Provided an expired/invalid JWT access token.

Expected:
Authentication should fail.

Actual:
403 Forbidden returned.

Response:
{
    "detail": "Given token not valid for any token type",
    "code": "token_not_valid"
}

Status:
PASS

### Test Case: Internal Server Error

Endpoint:
POST /api/jobs/create/

Action:
Attempted to create a job.

Expected:
Job creation success.

Actual:
500 Internal Server Error returned.

Response:
Django HTML Debug Error Page

Status:
BUG FOUND

## Internal Server Error Investigation

Endpoint:
POST /api/jobs/create/

Observation:
A 500 Internal Server Error was observed during early testing.

Re-testing after obtaining a valid employer JWT token produced:

201 Created

Conclusion:
The issue was caused by an invalid/expired authentication state rather than a backend code defect.

Status:
RESOLVED

500 Internal Server Error Investigation

Initial Observation:
POST /api/jobs/create/ returned 500.

Root Cause:
Expired/invalid authentication token was used.

Retest:
Using a valid employer token returned:

201 Created

Status:
Resolved

#ANOTHER DAY BUG REPORT##day29

Bug 1
Issue
Duplicate application allowed.
Fix
Added duplicate application check.
Application.objects.filter(
    candidate=request.user.candidate,
    job=job
).exists()
Result
Already applied
is returned.
________________________________________
Bug 2
Issue
Candidate status always started as
APPLIED
even before ATS evaluation.
Fix
Changed default flow to
UNDER_REVIEW
ATS now decides whether candidate is shortlisted.
________________________________________
Bug 3
Issue
Email was being sent twice.
Cause
Duplicate email notification function call.
Fix
Removed duplicate call.
________________________________________
Bug 4
Issue
Employer could access other employer applications.
Fix
Ownership validation.
if application.job.employer != request.user.employer:
returns
403 Forbidden
________________________________________
Bug 5
Issue
Unauthorized users could access protected APIs.
Fix
JWT Authentication
IsAuthenticated
permission added.
