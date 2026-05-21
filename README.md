# Mediterranean College Alumni Portal

Standalone 5CM519 CW2 Flask + SQLite product for the Mediterranean College Alumni Office.

## Purpose

This web application supports alumni registration, personal profile submission, profile editing, school-based alumni grouping, and administrative approval.

## Features

- Visitor application form for new alumni
- Applied Alumni accounts with private pending profiles
- Registered Alumni accounts with editable public/private profiles
- Admin dashboard for approving and rejecting applications
- Mediterranean College school grouping
- Public approved alumni directory
- SQLite relational database with users, roles, schools, profiles, applications, and audit logs
- Basic tests for public pages, application submission, admin approval, and access control

## Requirements

- Python 3.11+
- Flask
- pytest

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run Locally

```bash
flask --app alumni_app run --debug
```

On Windows, from the original coursework workspace with the included virtual environment:

```powershell
.\.venv\Scripts\python.exe -m flask --app alumni_app run --debug
```

Open:

```text
http://127.0.0.1:5000/alumni/
```

## Demo Users

- Admin: `admin@mc-alumni.test` / `AdminPass123!`
- Registered Alumni: `alumni@mc-alumni.test` / `AlumniPass123!`
- Applied Alumni: `pending@mc-alumni.test` / `PendingPass123!`

## Run Tests

```bash
pytest tests/test_alumni_portal.py
```

Or with the included Windows virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_alumni_portal.py
```

## Database

The SQLite database is created automatically on first run in:

```text
instance/alumni_portal.sqlite
```

The database file is ignored by Git because it is runtime data.
