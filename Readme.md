# Zecpath — AI-Powered Job Portal Backend

Zecpath is a Django REST Framework backend for an AI-assisted job portal that connects **candidates** and **employers**, with automated resume screening and interview scoring built in.

Live API (deployed on AWS EC2): `http://zecpath-fayis.duckdns.org/`
API Docs (Swagger / drf-spectacular): `http://zecpath-fayis.duckdns.org/api/docs/`

---

## Features

- **Authentication** — JWT-based auth (via `djangorestframework-simplejwt`) for Candidates, Employers, and Admins
- **Job Portal Core** — Job postings, applications, saved jobs, employer/candidate profiles
- **ATS Resume Scoring** — Upload a resume (PDF/DOCX), automatically extract skills, education, and experience, and score it against a job's requirements
- **AI Interview Flow** — Auto-generated interview questions and automated answer scoring after a candidate is shortlisted
- **Payments** — Razorpay integration for premium features, with signature verification
- **Cloud File Storage** — Resumes stored securely on AWS S3 (private bucket, presigned URLs, least-privilege IAM user)
- **Production-Grade Data Layer** — PostgreSQL with connection pooling, Redis-based query caching, and automated daily backups with tested restore procedures
- **Tested** — 21 automated tests covering signup, job posting, AI interview scoring, and payments

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Framework | Django, Django REST Framework |
| Database | PostgreSQL (both production and local dev) |
| Caching | Redis |
| Auth | JWT (simplejwt) |
| Cloud Storage | AWS S3 (django-storages, boto3) |
| Deployment | AWS EC2, Nginx, Gunicorn (systemd service) |
| Payments | Razorpay |
| API Docs | drf-spectacular (OpenAPI / Swagger) |

---

## Project Structure

```
zecpath-backend/
├── core/
│   ├── models.py          # User, Candidate, Employer, Job, Application, SavedJob
│   ├── utils.py             # Resume parsing & ATS scoring logic
│   ├── tasks.py              # Celery background tasks (interviews, reminders, emails)
│   └── services/
│       ├── ai_bridge.py            # AI interview simulation service
│       ├── application_service.py  # Email notifications, shortlisting logic
│       └── reminder_service.py     # Interview reminder scheduling
│   └── views/
│       ├── resume.py        # Resume upload & ATS parsing API
│       └── ...
├── manage.py
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Getting Started (Local Development)

```bash
# Clone the repo
git clone https://github.com/pachufayis2005-dev/zecpath-backend.git
cd zecpath-backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create a .env file (see Environment Variables below)

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

### Environment Variables

Create a `.env` file in the project root with:

```
SECRET_KEY=your-django-secret-key
DEBUG=True

DB_NAME=your-local-db-name
DB_USER=your-local-db-user
DB_PASSWORD=your-local-db-password
DB_HOST=127.0.0.1
DB_PORT=5432

AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-s3-bucket
AWS_S3_REGION_NAME=ap-south-1

RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret
RAZORPAY_WEBHOOK_SECRET=your-razorpay-webhook-secret
```

Note: A local PostgreSQL server must be running, and the `DB_USER` needs `CREATEDB` privilege to run the test suite (Django creates a temporary test database).

---

## Running Tests

```bash
python manage.py test
```

All 21 tests (signup, job posting, AI interview flow, and payment verification) pass against PostgreSQL.

---

## Logging

Application activity (interview processing, email notifications, reminders) is logged via Python's `logging` module:
- `logs/django_app.log` — INFO level and above (routine activity)
- `logs/django_errors.log` — ERROR level and above (failures)

---

## Deployment

Deployed on an AWS EC2 instance (Amazon Linux 2023) with:
- **Gunicorn** running as a systemd service (auto-restarts on crash/reboot)
- **Nginx** as a reverse proxy
- **PostgreSQL** as the production database, with Redis for query caching
- Daily automated backups via a cron job (`pg_dump`, 7-day retention, tested restore procedure)

---

## API Documentation

Interactive API docs are auto-generated with drf-spectacular and available at `/api/docs/` once the server is running.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Author

**Muhammed Fayis VB**
Python & Django Backend Developer
📧 pachufayis2005@gmail.com