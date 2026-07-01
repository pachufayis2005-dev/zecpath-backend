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

