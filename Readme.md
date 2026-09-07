# Zecpath — AI-Powered Job Portal Backend

Zecpath is a Django REST Framework backend for an AI-assisted job portal that connects **candidates** and **employers**, with automated resume screening and interview scoring built in.

Live API (deployed on AWS EC2): `http://<your-server-ip>/` — *replace with your domain/IP or leave blank if not public-facing*
API Docs (Swagger / drf-spectacular): `http://<your-server-ip>/api/docs/` — *replace with your actual docs URL*

---

## Features

- **Authentication** — JWT-based auth (via `djangorestframework-simplejwt`) for Candidates, Employers, and Admins
- **Job Portal Core** — Job postings, applications, saved jobs, employer/candidate profiles
- **ATS Resume Scoring** — Upload a resume (PDF/DOCX), automatically extract skills, education, and experience, and score it against a job's requirements
- **AI Interview Flow** — Auto-generated interview questions and automated answer scoring after a candidate is shortlisted
- **Payments** — Razorpay integration for premium features, with signature verification
- **Cloud File Storage** — Resumes stored securely on AWS S3 (private bucket, presigned URLs, least-privilege IAM user)
- **Production-Grade Data Layer** — PostgreSQL with connection pooling, Redis-based query caching, and automated daily backups with tested restore procedures
- **Tested** — 17 automated tests covering signup, job posting, AI interview scoring, and payments

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Framework | Django, Django REST Framework |
| Database | PostgreSQL (production), SQLite (local dev) |
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
│   ├── utils.py            # Resume parsing & ATS scoring logic
│   ├── permissions.py      # Custom DRF permissions (e.g. IsCandidate)
│   └── views/
│       ├── resume.py        # Resume upload & ATS parsing API
│       └── ...
├── manage.py
├── requirements.txt
└── README.md
```
*(Update this tree if your actual folder names differ.)*

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

# Copy environment variables template and fill in your own values
cp .env.example .env

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

### Environment Variables

Create a `.env` file with (see `.env.example`):

```
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/zecpath_db
REDIS_URL=redis://localhost:6379/1
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-s3-bucket
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret
```

---

## Running Tests

```bash
python manage.py test
```

All 17 tests (signup, job posting, AI interview flow, and payment verification) pass against PostgreSQL.

---

## Deployment

Deployed on an AWS EC2 instance (Amazon Linux) with:
- **Gunicorn** running as a systemd service (auto-restarts on crash/reboot)
- **Nginx** as a reverse proxy
- **PostgreSQL** as the production database, with Redis for query caching
- Daily automated backups via a cron job (`pg_dump`, 7-day retention)

---

## API Documentation

For detailed authentication flow, all endpoints, error codes, and rate limits, see the [API Developer Guide](docs/API_GUIDE.md).

Interactive API docs are auto-generated with drf-spectacular and available at `/api/docs/` once the server is running.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Author

**Muhammed Fayis VB**
Python & Django Backend Developer
📧 pachufayis2005@gmail.com