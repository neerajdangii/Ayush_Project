# LIMS (Django + PostgreSQL)

## Run locally
1. Create and activate venv:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure env:
```bash
cp .env.example .env
```

4. Ensure PostgreSQL is running and DB credentials in `.env` are correct.

5. Run migrations and create admin user:
```bash
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py createsuperuser
```

6. Start server:
```bash
python3 manage.py runserver
```

Open: `http://127.0.0.1:8000/accounts/login/`

## VPS test deployment notes
- For a VPS test deployment without HTTPS, keep these values disabled:
  - `DJANGO_SECURE_SSL_REDIRECT=False`
  - `DJANGO_SESSION_COOKIE_SECURE=False`
  - `DJANGO_CSRF_COOKIE_SECURE=False`
  - `DJANGO_SECURE_HSTS_SECONDS=0`
- For PostgreSQL on Docker Compose, either set `DATABASE_URL` or set `DJANGO_USE_POSTGRES=True` with the `POSTGRES_*` variables.

## Main pages
- Login: `/accounts/login/`
- Dashboard: `/`
- New Booking: `/bookings/new/`
- Bookings: `/bookings/`
- Reports: `/reports/`

## How database storage works
Data is stored in PostgreSQL via Django ORM:

1. `Booking` rows are saved in `bookings_booking`.
2. `Report` rows are saved in `reports_report`.
3. On booking approval:
   - booking status changes to `approved`
   - one report row is created (or reused) for that booking
4. `Report.booking` is one-to-one with booking, so one booking maps to one report.

## Verify stored data
After creating/approving some records in UI, run:

```bash
python3 manage.py show_data
```

This prints recent bookings/reports from PostgreSQL.

You can also check with SQL directly:

```bash
psql -h 127.0.0.1 -U postgres -d lims_db
```

Inside `psql`:

```sql
SELECT booking_number, client_name, status, created_at
FROM bookings_booking
ORDER BY created_at DESC
LIMIT 10;

SELECT report_number, status, created_at
FROM reports_report
ORDER BY created_at DESC
LIMIT 10;
```
