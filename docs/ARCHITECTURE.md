# Zecpath Backend — Architecture Documentation

This document describes Zecpath's system architecture: how the major
components fit together, how data flows through the system, and how the
database is structured.

---

## 1. System Breakdown

Zecpath is built as a single Django monolith with logically separate modules
inside it. Each module owns a distinct responsibility:

**Authentication** — JWT-based auth (`djangorestframework-simplejwt`) issuing
short-lived access tokens (30 min) and longer-lived refresh tokens (1 day,
rotated and blacklisted after use). Three roles: Candidate, Employer, Admin,
distinguished by the `User.role` field.

**Job Portal Core** — Job postings, applications, saved jobs, and
candidate/employer profiles. This is the transactional heart of the system:
`Job`, `Application`, `SavedJob` models with indexes on frequently filtered
fields (status, location, job type) to keep listing/search queries fast as
the job pool grows.

**ATS Engine** — Resume parsing (`core/utils.py`: text, skills, experience,
and education extraction from PDF/DOCX) followed by a rules-based scoring
engine (`calculate_ats_score`) that compares a candidate's parsed resume
against a job's requirements, producing a numeric match score
(`Application.ats_score`) used for auto-shortlisting.

**AI Automation** — A simulated AI interview pipeline: once a candidate is
shortlisted, an `InterviewCall` is created, which triggers an
`AIInterviewSession` with a rule-based question engine
(`AIQuestion`/category-based) and an answer evaluator that scores each
`AIAnswer` on confidence, relevance, and completeness. Fully self-contained —
no external AI API calls, by design, for cost and reliability while learning
the system.

**Payments & Billing** — Razorpay integration for subscription payments.
Covers order creation, signature verification, capture, and Razorpay
webhooks, backed by `PaymentTransaction`, `BillingHistory`, `RefundRecord`,
and `FinancialAuditLog` for a full financial audit trail.

**Background Processing** — Celery + Redis handle asynchronous work: AI
interview call processing, email notifications (with retry logic), and
interview reminders, so these don't block the request/response cycle.

**Deployment Layer** — Gunicorn (systemd-managed, auto-restart) behind Nginx
as a reverse proxy, PostgreSQL as the primary datastore, Redis for both
Celery's broker and Django's query cache, and AWS S3 for resume file storage.

---

## 2. High-Level Architecture

```mermaid
graph TD
    Client[Client / Frontend] -->|HTTPS| Nginx[Nginx Reverse Proxy]
    Nginx --> Gunicorn[Gunicorn WSGI Server]
    Gunicorn --> Django[Django REST Framework App]

    Django --> Auth[Auth Module<br/>JWT]
    Django --> JobPortal[Job Portal Core]
    Django --> ATS[ATS Engine<br/>Resume Parsing + Scoring]
    Django --> AIInterview[AI Interview Module]
    Django --> Billing[Payments & Billing]

    Django --> Postgres[(PostgreSQL)]
    Django --> Redis[(Redis<br/>Cache + Celery Broker)]
    Django --> S3[(AWS S3<br/>Resume Storage)]

    Celery[Celery Workers] --> Redis
    Celery --> AIInterview
    Celery --> Reminders[Email/Reminder Service]

    Billing --> Razorpay[Razorpay API]
```

---

## 3. Service Interaction Diagram

Shows how a resume upload flows through the ATS engine, and how a shortlist
triggers the AI interview pipeline asynchronously via Celery.

```mermaid
sequenceDiagram
    participant C as Candidate
    participant API as Django API
    participant ATS as ATS Engine
    participant S3 as AWS S3
    participant DB as PostgreSQL
    participant Q as Celery + Redis

    C->>API: POST /resume/parse/ (resume file)
    API->>S3: Store resume file
    API->>ATS: Extract text/skills/experience/education
    ATS->>DB: Save Candidate profile
    C->>API: POST /jobs/<id>/apply/
    API->>ATS: calculate_ats_score(job, resume)
    ATS->>DB: Save Application with ats_score
    API->>DB: auto_shortlist() if score >= threshold
    API->>Q: Queue process_interview_calls task
    Q->>DB: Create InterviewCall + AIInterviewSession
    Q->>C: (async) Interview questions generated
```

---

## 4. Database Schema (ERD)

### Core Domain — Users, Jobs, Applications

```mermaid
erDiagram
    User ||--o| Employer : "has profile"
    User ||--o| Candidate : "has profile"
    Employer ||--o{ Job : posts
    Candidate ||--o{ Application : submits
    Job ||--o{ Application : receives
    Candidate ||--o{ SavedJob : saves
    Job ||--o{ SavedJob : "saved as"
    Application ||--o| InterviewCall : triggers
    Employer ||--o{ AvailabilitySlot : offers
    Application ||--o| InterviewSchedule : "scheduled via"
    AvailabilitySlot ||--o| InterviewSchedule : "booked into"
    InterviewSchedule ||--o{ ReminderLog : generates

    User {
        string username
        string email
        string role
        bool is_verified
    }
    Job {
        string title
        string status
        string job_type
        int salary
    }
    Application {
        string status
        float ats_score
        datetime applied_at
    }
```

### AI Interview Domain

```mermaid
erDiagram
    InterviewCall ||--o| AIInterviewSession : starts
    AIInterviewSession ||--o{ AIQuestion : generates
    AIQuestion ||--o| AIAnswer : answered_by
    AIInterviewSession ||--o{ CallLog : logs
    InterviewCall ||--o{ AIEventLog : logs

    AIQuestion {
        string category
        text question
    }
    AIAnswer {
        float confidence_score
        float relevance_score
        float completeness_score
        float final_score
    }
```

### Billing Domain

```mermaid
erDiagram
    Employer ||--o{ UserSubscription : subscribes
    SubscriptionPlan ||--o{ UserSubscription : "defines"
    UserSubscription ||--o{ PaymentTransaction : "paid via"
    Employer ||--o{ PaymentTransaction : makes
    PaymentTransaction ||--o{ RefundRecord : "refunded via"
    PaymentTransaction ||--o{ BillingHistory : "recorded as"
    PaymentTransaction ||--o{ FinancialAuditLog : audited

    SubscriptionPlan {
        string name
        decimal price
        string billing_cycle
        int job_post_limit
    }
    PaymentTransaction {
        decimal amount
        string status
        string razorpay_order_id
    }
```

---

## 5. Key User Flows

### Candidate Flow

```mermaid
flowchart LR
    A[Sign Up as Candidate] --> B[Build Profile / Upload Resume]
    B --> C[Browse / Search Jobs]
    C --> D[Apply to Job]
    D --> E[ATS Score Calculated]
    E --> F{Score >= Threshold?}
    F -->|Yes| G[Auto-Shortlisted]
    F -->|No| H[Under Review]
    G --> I[AI Interview Triggered]
    I --> J[Answer Questions]
    J --> K[Interview Scored]
    K --> L[Selected / Rejected]
```

### Employer Flow

```mermaid
flowchart LR
    A[Sign Up as Employer] --> B[Admin Approval]
    B --> C[Post Job]
    C --> D[Receive Applications]
    D --> E[View Ranked Candidates]
    E --> F[Review / Shortlist]
    F --> G[Set Availability Slots]
    G --> H[Candidate Books Interview]
    H --> I[Review Interview Score]
    I --> J[Select Candidate]
```

### Job Lifecycle

```mermaid
flowchart LR
    A[Job Created - Active] --> B[Receiving Applications]
    B --> C{Employer Action}
    C -->|Close manually| D[Closed]
    C -->|Flagged as Spam| E[Removed by Admin]
    B --> F[Featured - promoted]
```

### Payment Flow

```mermaid
sequenceDiagram
    participant E as Employer
    participant API as Django API
    participant RP as Razorpay

    E->>API: POST /payments/create-order/
    API->>RP: Create order
    RP-->>API: order_id
    API-->>E: order_id + amount
    E->>RP: Complete payment (Razorpay checkout)
    RP-->>E: payment_id + signature
    E->>API: POST /payments/verify/ (payment_id, signature)
    API->>API: Verify HMAC signature locally
    API->>API: Update PaymentTransaction, UserSubscription
    RP->>API: POST /payments/webhook/ (async confirmation)
```

---

## 6. Module-Wise Reference

| Module | Key Files |
|---|---|
| Auth | `core/views/auth.py` |
| Jobs | `core/views/jobs.py`, `core/models.py::Job` |
| Applications | `core/views/applications.py`, `core/models.py::Application` |
| ATS Engine | `core/utils.py`, `core/services/application_service.py` |
| AI Interview | `core/services/ai_bridge.py`, `core/services/answer_evaluator.py`, `core/services/question_engine.py` |
| Reminders | `core/services/reminder_service.py`, `core/tasks.py` |
| Payments | `core/views/billing.py`, `core/services/payment_service.py`, `core/services/financial_security_service.py` |
| Analytics | `core/services/analytics_service.py` |
| Admin | `core/views/admin.py` |

For endpoint-level detail, see [API_REFERENCE.md](API_REFERENCE.md). For
deployment steps, see [SETUP_GUIDE.md](SETUP_GUIDE.md).