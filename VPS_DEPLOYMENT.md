# VPS Deployment Guide

This guide explains how to run this Django application on a VPS using Docker Compose.

It is written for your current setup:
- internal team testing
- low traffic
- no SSL for now
- no Nginx for now

## 1. Prerequisites

You need a Linux VPS with:
- Docker installed
- Docker Compose plugin installed
- Git installed

If Docker is not installed, install it first on the VPS.

## 2. Copy the project to the VPS

SSH into the VPS:

```bash
ssh root@your-vps-ip
```

Clone the project:

```bash
git clone <your-repo-url>
cd Ayush_Project
```

If the project is already on the VPS, just go to the project folder.

## 3. Configure environment file

This project uses `.env.prod` for Docker Compose.

Open `.env.prod` and update these values:

```env
DJANGO_SECRET_KEY=put-a-long-random-secret-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=*
DJANGO_CSRF_TRUSTED_ORIGINS=http://your-vps-ip
DJANGO_TIME_ZONE=Asia/Kolkata

DJANGO_USE_POSTGRES=True
DJANGO_SECURE_PROXY_SSL_HEADER=True
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SESSION_COOKIE_SECURE=False
DJANGO_CSRF_COOKIE_SECURE=False
DJANGO_SECURE_HSTS_SECONDS=0
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=False
DJANGO_SECURE_HSTS_PRELOAD=False

DATABASE_URL=

POSTGRES_DB=lims_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=replace-with-strong-db-password
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

Notes:
- `DJANGO_ALLOWED_HOSTS=*` is okay for your current internal testing
- `DJANGO_CSRF_TRUSTED_ORIGINS` should contain the exact origin you use in browser
- if you use a domain later, add it there too

Example:

```env
DJANGO_CSRF_TRUSTED_ORIGINS=http://123.45.67.89
```

If you use a custom port, include it:

```env
DJANGO_CSRF_TRUSTED_ORIGINS=http://123.45.67.89:8000
```

## 4. Build and start the containers

Run:

```bash
docker compose up -d --build
```

This does the following:
- builds the Django image
- starts PostgreSQL
- runs Django migrations
- collects static files
- starts Gunicorn on port `8000`

## 5. Check if containers are running

Run:

```bash
docker compose ps
```

To see logs:

```bash
docker compose logs -f
```

To see only web logs:

```bash
docker compose logs -f web
```

## 6. Create admin user

After containers are running, create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

## 7. Open the application

Open this in your browser:

```text
http://your-vps-ip:8000/accounts/login/
```

## 8. Useful commands

Stop containers:

```bash
docker compose down
```

Restart containers:

```bash
docker compose restart
```

Rebuild after code changes:

```bash
docker compose up -d --build
```

Run Django commands manually:

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py migrate
docker compose exec web python manage.py show_data
```

## 9. If something does not open

Check these points:

1. Make sure port `8000` is open in the VPS firewall.
2. Make sure Docker containers are running.
3. Make sure `DJANGO_ALLOWED_HOSTS` is correct.
4. Make sure `DJANGO_CSRF_TRUSTED_ORIGINS` matches the browser URL.
5. Check logs:

```bash
docker compose logs -f web
docker compose logs -f db
```

## 10. PDF generation note

This app generates PDFs using WeasyPrint.

The Docker image already installs the system libraries needed for this. If PDF generation fails, check web logs first:

```bash
docker compose logs -f web
```

## 11. Updating the app later

If you pull new code on the VPS:

```bash
git pull
docker compose up -d --build
```

## 12. Data persistence

Database data is stored in a Docker volume, so it stays available even if containers are recreated.

Static files are also stored in a Docker volume.

## 13. Current scope of this setup

This setup is good for:
- internal testing
- team demo usage
- low traffic VPS deployment

This setup does not yet include:
- SSL/HTTPS
- Nginx reverse proxy
- domain hardening
- production monitoring

Those can be added later if needed.
