# ZecPath Backend API Documentation

---

# Authentication APIs

## 1. User Signup

### Endpoint

POST /api/signup/

### Authentication

Not Required

### Request Body

```json
{
    "username": "candidate1",
    "email": "candidate@test.com",
    "phone": "9999999999",
    "role": "CANDIDATE",
    "password": "test123"
}
```

### Success Response

Status Code:

201 Created

Example:

```json
{
    "username": "candidate1",
    "email": "candidate@test.com",
    "phone": "9999999999",
    "role": "CANDIDATE"
}
```

---

## 2. User Login

### Endpoint

POST /api/login/

### Authentication

Not Required

### Request Body

```json
{
    "username": "candidate1",
    "password": "test123"
}
```

### Success Response

Status Code:

200 OK

Example:

```json
{
    "refresh": "...",
    "access": "..."
}
```

---

# Protected APIs

## 3. User Test API

### Endpoint

GET /api/users/test/

### Authentication

Bearer Token Required

### Success Response

Status Code:

200 OK

Example:

```json
{
    "message": "Protected API Working",
    "user": "candidate1",
    "role": "CANDIDATE"
}
```

---

## 4. Admin Test API

### Endpoint

GET /api/admin/test/

### Authentication

Bearer Token Required

### Permission

ADMIN Only

### Failure Response

Status Code:

403 Forbidden

Example:

```json
{
    "detail": "You do not have permission to perform this action."
}
```

---

# Candidate APIs

## 5. Candidate Profile

### Endpoint

GET /api/candidate/profile/

### Authentication

Bearer Token Required

### Permission

Candidate Only

### Success Response

Status Code:

200 OK

Example:

```json
{
    "id": 5,
    "skills": "python,django",
    "education": "B.tech",
    "experience": "2 years",
    "expected_salary": 60000
}
```

---

# Job APIs

## 6. List Jobs

### Endpoint

GET /api/jobs/

### Authentication

Not Required

### Features

* Pagination
* Search
* Status Filter
* Date Filter

---

## Search Example

GET /api/jobs/?search=python

---

## Status Filter Example

GET /api/jobs/?status=CLOSED

---

## Date Filter Example

GET /api/jobs/?date=2026-07-02

---

## Pagination Example

GET /api/jobs/?page=2&page_size=3

---

## 7. Create Job

### Endpoint

POST /api/jobs/create/

### Authentication

Bearer Token Required

### Permission

Employer Only

### Request Body

```json
{
    "title": "Java Developer",
    "description": "Backend Developer",
    "status": "CLOSED"
}
```

### Success Response

Status Code:

201 Created
