import sqlite3
from datetime import datetime, timezone

from flask import current_app, g
from werkzeug.security import generate_password_hash


SCHEMA = """
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (role) REFERENCES roles (name)
);

CREATE TABLE IF NOT EXISTS schools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alumni_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    school_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    student_id TEXT,
    graduation_year INTEGER NOT NULL,
    course TEXT NOT NULL,
    job_title TEXT,
    company TEXT,
    location TEXT,
    linkedin_url TEXT,
    bio TEXT NOT NULL,
    visibility TEXT NOT NULL DEFAULT 'private',
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (school_id) REFERENCES schools (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'pending',
    submitted_at TEXT NOT NULL,
    reviewed_by INTEGER,
    reviewed_at TEXT,
    admin_notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    actor_user_id INTEGER,
    target_user_id INTEGER,
    details TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (actor_user_id) REFERENCES users (id) ON DELETE SET NULL,
    FOREIGN KEY (target_user_id) REFERENCES users (id) ON DELETE SET NULL
);
"""

ROLE_SEED = [
    ("admin", "Administrative users can approve applications and manage schools."),
    ("registered_alumni", "Approved alumni can maintain profiles and browse the directory."),
    ("applied_alumni", "Applicants can track their application and update submitted details."),
]

SCHOOL_SEED = [
    ("School of Computing", "Software engineering, cyber security, data, networks and digital systems."),
    ("School of Business", "Business management, marketing, finance, tourism and entrepreneurship."),
    ("School of Psychology", "Psychology, counselling and social sciences."),
    ("School of Health Sciences", "Health, wellbeing and applied healthcare programmes."),
    ("School of Education", "Education, teaching practice and lifelong learning."),
]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    database = g.pop("db", None)
    if database is not None:
        database.close()


def init_db():
    database = get_db()
    database.executescript(SCHEMA)
    seed_roles(database)
    seed_schools(database)
    seed_users(database)
    database.commit()


def seed_roles(database):
    for name, description in ROLE_SEED:
        database.execute(
            "INSERT OR IGNORE INTO roles (name, description) VALUES (?, ?)",
            (name, description),
        )


def seed_schools(database):
    for name, description in SCHOOL_SEED:
        database.execute(
            "INSERT OR IGNORE INTO schools (name, description) VALUES (?, ?)",
            (name, description),
        )


def seed_users(database):
    if database.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        return

    now = utc_now()
    admin_id = create_user("admin@mc-alumni.test", generate_password_hash("AdminPass123!"), "admin", database)
    alumni_id = create_user("alumni@mc-alumni.test", generate_password_hash("AlumniPass123!"), "registered_alumni", database)
    applied_id = create_user("pending@mc-alumni.test", generate_password_hash("PendingPass123!"), "applied_alumni", database)

    computing = get_school_by_name("School of Computing", database)["id"]
    business = get_school_by_name("School of Business", database)["id"]

    create_profile(
        alumni_id,
        computing,
        {
            "full_name": "Maria Antoniou",
            "student_id": "MC201901",
            "graduation_year": 2022,
            "course": "BSc Computer Science",
            "job_title": "Junior Software Developer",
            "company": "Athens Digital Lab",
            "location": "Athens, Greece",
            "linkedin_url": "https://linkedin.com/in/example",
            "bio": "Mediterranean College graduate working in web application development.",
            "visibility": "public",
        },
        database,
    )
    database.execute(
        "INSERT INTO applications (user_id, status, submitted_at, reviewed_by, reviewed_at, admin_notes) VALUES (?, 'approved', ?, ?, ?, ?)",
        (alumni_id, now, admin_id, now, "Seed approved alumni account."),
    )

    create_profile(
        applied_id,
        business,
        {
            "full_name": "Nikos Georgiou",
            "student_id": "MC202103",
            "graduation_year": 2024,
            "course": "BA Business Management",
            "job_title": "Marketing Assistant",
            "company": "Local Growth Agency",
            "location": "Thessaloniki, Greece",
            "linkedin_url": "",
            "bio": "Pending alumni applicant awaiting office approval.",
            "visibility": "private",
        },
        database,
    )
    database.execute(
        "INSERT INTO applications (user_id, status, submitted_at) VALUES (?, 'pending', ?)",
        (applied_id, now),
    )
    log_event("seed_data_created", admin_id, None, "Demo users and profiles created.", database)


def create_user(email, password_hash, role="applied_alumni", database=None):
    database = database or get_db()
    cur = database.execute(
        "INSERT INTO users (email, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (email.strip().lower(), password_hash, role, utc_now()),
    )
    return cur.lastrowid


def get_user_by_id(user_id):
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_by_email(email):
    return get_db().execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip().lower(),)).fetchone()


def list_schools():
    return get_db().execute("SELECT * FROM schools ORDER BY name").fetchall()


def get_school_by_name(name, database=None):
    database = database or get_db()
    return database.execute("SELECT * FROM schools WHERE name = ?", (name,)).fetchone()


def add_school(name, description):
    database = get_db()
    database.execute(
        "INSERT INTO schools (name, description) VALUES (?, ?)",
        (name.strip(), description.strip()),
    )
    database.commit()


def create_profile(user_id, school_id, data, database=None):
    database = database or get_db()
    database.execute(
        """
        INSERT INTO alumni_profiles (
            user_id, school_id, full_name, student_id, graduation_year, course,
            job_title, company, location, linkedin_url, bio, visibility, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            school_id,
            data["full_name"].strip(),
            data.get("student_id", "").strip(),
            int(data["graduation_year"]),
            data["course"].strip(),
            data.get("job_title", "").strip(),
            data.get("company", "").strip(),
            data.get("location", "").strip(),
            data.get("linkedin_url", "").strip(),
            data["bio"].strip(),
            data.get("visibility", "private"),
            utc_now(),
        ),
    )


def update_profile(user_id, school_id, data):
    database = get_db()
    database.execute(
        """
        UPDATE alumni_profiles
        SET school_id = ?, full_name = ?, student_id = ?, graduation_year = ?, course = ?,
            job_title = ?, company = ?, location = ?, linkedin_url = ?, bio = ?, visibility = ?, updated_at = ?
        WHERE user_id = ?
        """,
        (
            school_id,
            data["full_name"].strip(),
            data.get("student_id", "").strip(),
            int(data["graduation_year"]),
            data["course"].strip(),
            data.get("job_title", "").strip(),
            data.get("company", "").strip(),
            data.get("location", "").strip(),
            data.get("linkedin_url", "").strip(),
            data["bio"].strip(),
            data.get("visibility", "private"),
            utc_now(),
            user_id,
        ),
    )
    database.commit()


def get_profile_for_user(user_id):
    return get_db().execute(
        """
        SELECT p.*, s.name AS school_name, u.email, u.role
        FROM alumni_profiles p
        JOIN schools s ON s.id = p.school_id
        JOIN users u ON u.id = p.user_id
        WHERE p.user_id = ?
        """,
        (user_id,),
    ).fetchone()


def list_profiles(school_id=None, query="", include_private=False):
    params = []
    where = []
    if not include_private:
        where.append("p.visibility = 'public'")
        where.append("u.role = 'registered_alumni'")
    if school_id:
        where.append("p.school_id = ?")
        params.append(school_id)
    if query:
        where.append("(p.full_name LIKE ? OR p.course LIKE ? OR p.company LIKE ? OR p.job_title LIKE ?)")
        q = f"%{query}%"
        params.extend([q, q, q, q])
    clause = "WHERE " + " AND ".join(where) if where else ""
    return get_db().execute(
        f"""
        SELECT p.*, s.name AS school_name, u.email, u.role
        FROM alumni_profiles p
        JOIN schools s ON s.id = p.school_id
        JOIN users u ON u.id = p.user_id
        {clause}
        ORDER BY s.name, p.graduation_year DESC, p.full_name
        """,
        params,
    ).fetchall()


def create_application(user_id):
    database = get_db()
    database.execute(
        "INSERT INTO applications (user_id, status, submitted_at) VALUES (?, 'pending', ?)",
        (user_id, utc_now()),
    )
    database.commit()


def get_application_for_user(user_id):
    return get_db().execute("SELECT * FROM applications WHERE user_id = ?", (user_id,)).fetchone()


def list_applications(status=None):
    params = []
    where = ""
    if status:
        where = "WHERE a.status = ?"
        params.append(status)
    return get_db().execute(
        f"""
        SELECT a.*, p.full_name, p.student_id, p.course, p.graduation_year, p.bio,
               s.name AS school_name, u.email, u.role
        FROM applications a
        JOIN users u ON u.id = a.user_id
        JOIN alumni_profiles p ON p.user_id = u.id
        JOIN schools s ON s.id = p.school_id
        {where}
        ORDER BY a.submitted_at DESC
        """,
        params,
    ).fetchall()


def review_application(application_id, status, reviewer_id, notes=""):
    database = get_db()
    application = database.execute("SELECT * FROM applications WHERE id = ?", (application_id,)).fetchone()
    if application is None:
        return False
    role = "registered_alumni" if status == "approved" else "applied_alumni"
    visibility = "public" if status == "approved" else "private"
    database.execute("UPDATE users SET role = ? WHERE id = ?", (role, application["user_id"]))
    database.execute("UPDATE alumni_profiles SET visibility = ?, updated_at = ? WHERE user_id = ?", (visibility, utc_now(), application["user_id"]))
    database.execute(
        "UPDATE applications SET status = ?, reviewed_by = ?, reviewed_at = ?, admin_notes = ? WHERE id = ?",
        (status, reviewer_id, utc_now(), notes.strip(), application_id),
    )
    log_event(f"application_{status}", reviewer_id, application["user_id"], notes, database)
    database.commit()
    return True


def stats():
    database = get_db()
    return {
        "schools": database.execute("SELECT COUNT(*) FROM schools").fetchone()[0],
        "registered": database.execute("SELECT COUNT(*) FROM users WHERE role = 'registered_alumni'").fetchone()[0],
        "pending": database.execute("SELECT COUNT(*) FROM applications WHERE status = 'pending'").fetchone()[0],
    }


def log_event(event, actor_user_id=None, target_user_id=None, details="", database=None):
    database = database or get_db()
    database.execute(
        "INSERT INTO audit_logs (event, actor_user_id, target_user_id, details, created_at) VALUES (?, ?, ?, ?, ?)",
        (event, actor_user_id, target_user_id, details, utc_now()),
    )
