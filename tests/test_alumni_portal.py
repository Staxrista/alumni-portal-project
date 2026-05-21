import pytest

from alumni_portal import create_app
from alumni_portal import db


@pytest.fixture
def alumni_app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(tmp_path / "alumni-test.sqlite"),
        }
    )


@pytest.fixture
def alumni_client(alumni_app):
    return alumni_app.test_client()


def login(client, email, password):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def application_payload(email="new.alumni@example.test"):
    return {
        "email": email,
        "password": "Applicant123!",
        "full_name": "Eleni Papadopoulou",
        "student_id": "MC202599",
        "school_id": "1",
        "graduation_year": "2025",
        "course": "BSc Computer Science",
        "job_title": "Graduate Developer",
        "company": "Mediterranean Tech Hub",
        "location": "Athens, Greece",
        "linkedin_url": "https://linkedin.com/in/eleni-example",
        "bio": "Recent Mediterranean College graduate interested in alumni networking.",
    }


def test_home_and_directory_are_public(alumni_client):
    home = alumni_client.get("/alumni/")
    directory = alumni_client.get("/alumni/directory")

    assert home.status_code == 200
    assert directory.status_code == 200
    assert b"Mediterranean College Alumni Office" in home.data
    assert b"Maria Antoniou" in directory.data


def test_visitor_can_submit_application(alumni_app, alumni_client):
    response = alumni_client.post("/alumni/apply", data=application_payload(), follow_redirects=True)

    assert response.status_code == 200
    assert b"Application submitted" in response.data
    with alumni_app.app_context():
        user = db.get_user_by_email("new.alumni@example.test")
        assert user is not None
        assert user["role"] == "applied_alumni"
        application = db.get_application_for_user(user["id"])
        assert application["status"] == "pending"


def test_admin_can_approve_application(alumni_app, alumni_client):
    alumni_client.post("/alumni/apply", data=application_payload("approve.me@example.test"))
    with alumni_app.app_context():
        user = db.get_user_by_email("approve.me@example.test")
        application_id = db.get_application_for_user(user["id"])["id"]

    login_response = login(alumni_client, "admin@mc-alumni.test", "AdminPass123!")
    assert b"Alumni office controls" in login_response.data
    response = alumni_client.post(
        f"/admin/applications/{application_id}/approve",
        data={"admin_notes": "Verified test applicant."},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Application approved" in response.data
    with alumni_app.app_context():
        user = db.get_user_by_email("approve.me@example.test")
        profile = db.get_profile_for_user(user["id"])
        application = db.get_application_for_user(user["id"])
        assert user["role"] == "registered_alumni"
        assert profile["visibility"] == "public"
        assert application["status"] == "approved"


def test_admin_profile_links_do_not_render_and_profile_redirects(alumni_client):
    response = login(alumni_client, "admin@mc-alumni.test", "AdminPass123!")

    assert response.status_code == 200
    assert b"My Profile" not in response.data
    profile_response = alumni_client.get("/alumni/profile", follow_redirects=True)
    assert b"No alumni profile is linked" in profile_response.data
    assert b"Alumni office controls" in profile_response.data


def test_non_admin_cannot_open_admin_dashboard(alumni_client):
    login(alumni_client, "alumni@mc-alumni.test", "AlumniPass123!")
    response = alumni_client.get("/admin/", follow_redirects=True)

    assert response.status_code == 200
    assert b"You do not have permission" in response.data
    assert b"Register alumni, approve applications" in response.data
