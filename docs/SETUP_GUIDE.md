# Zecpath Backend — Setup & Deployment Guide

This guide documents how to set up Zecpath from a blank server to a fully running
production instance, exactly as it is deployed today.

---

## 1. Prerequisites

- An AWS EC2 instance running Amazon Linux 2023 (or compatible)
- A domain or free dynamic DNS name (this project uses DuckDNS:
  `zecpath-fayis.duckdns.org`)
- SSH access to the server via a `.pem` key file
- A GitHub repository containing the project code

---

## 2. Initial Server Setup

Connect to the server:

```bash
ssh -i /path/to/your-key.pem ec2-user@<your-server-ip>
```

Update the system and install required packages:

```bash
sudo dnf update -y
sudo dnf install -y python3.12 python3.12-venv git nginx postgresql15-server redis6 cronie
```

---

## 3. Clone the Project

```bash
git clone https://github.com/pachufayis2005-dev/zecpath-backend.git
cd zecpath-backend
```

---

## 4. Python Environment

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 5. PostgreSQL Setup

Initialize and start Postgres:

```bash
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
```

Fix authentication to allow password login (edit `pg_hba.conf`, change the
`127.0.0.1/32` host line from `ident` to `md5`), then restart:

```bash
sudo systemctl restart postgresql
```

Create the database and user:

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE zecpath_db;
CREATE USER zecpath_user WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE zecpath_db TO zecpath_user;
ALTER USER zecpath_user CREATEDB;
\q
```

(The `CREATEDB` grant is required so Django's test suite can create its
temporary test database.)

---

## 6. Redis Setup

```bash
sudo systemctl enable --now redis6
```

Redis runs on `127.0.0.1:6379` by default — used for both Celery (DB 0) and
Django's query cache (DB 1).

---

## 7. Environment Variables

Create a `.env` file in the project root:

```
SECRET_KEY=your-django-secret-key
DEBUG=False

DB_NAME=zecpath_db
DB_USER=zecpath_user
DB_PASSWORD=your-secure-password
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

**Never commit `.env` to Git** — it is already excluded via `.gitignore`.

---

## 8. Django Setup

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

---

## 9. Gunicorn as a systemd Service

Create `/etc/systemd/system/gunicorn.service`:

```ini
[Unit]
Description=Gunicorn daemon for Zecpath backend
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/zecpath-backend
ExecStart=/home/ec2-user/zecpath-backend/venv/bin/gunicorn --bind 127.0.0.1:8000 backend.wsgi
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn
```

This ensures Gunicorn auto-starts on server reboot and auto-restarts if it
crashes.

---

## 10. Nginx Reverse Proxy

Create `/etc/nginx/conf.d/zecpath.conf`:

```nginx
server {
    listen 80;
    server_name zecpath-fayis.duckdns.org <your-server-ip>;

    location /static/ {
        alias /home/ec2-user/zecpath-backend/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Test and reload:

```bash
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx
```

---

## 11. Celery Worker & Beat (Background Tasks)

Set these up as systemd services the same way as Gunicorn, pointing at
`celery -A backend worker` and `celery -A backend beat`, so scheduled
reminders and AI interview processing run continuously in the background.

---

## 12. Automated Backups

A daily backup script (`~/backup_db.sh`) runs via cron at 2 AM, dumping the
database with `pg_dump`, compressing it, and deleting backups older than 7
days. Set it up with:

```bash
crontab -e
```

```
0 2 * * * /home/ec2-user/backup_db.sh
```

---

## 13. Deploying Updates

The standard workflow for pushing a code change to production:

```bash
# Locally: commit and push
git add .
git commit -m "your message"
git push

# On the server:
cd ~/zecpath-backend
git pull
source venv/bin/activate
pip install -r requirements.txt   # only if dependencies changed
python manage.py migrate          # only if models changed
sudo systemctl restart gunicorn
```

Always run `python manage.py test` locally before pushing, and
`python manage.py check` on the server before restarting Gunicorn, to catch
issues before they reach production.

---

## 14. Verifying the Deployment

```bash
sudo systemctl status gunicorn nginx postgresql redis6 --no-pager
tail -n 30 logs/django_errors.log
```

Then confirm the live site loads: `http://zecpath-fayis.duckdns.org/admin/`