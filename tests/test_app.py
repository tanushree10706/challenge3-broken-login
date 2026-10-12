import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app  # noqa: E402

FLAG = "TECH{sqli_login_bypass}"


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "test.db"),
                      "SECRET_KEY": "test-key", "CTF_FLAG": FLAG})
    return app.test_client()


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)


def test_homepage_and_login_form_load(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b'name="username"' in res.data and b'name="password"' in res.data
    assert FLAG.encode() not in res.data


def test_valid_credentials_work_without_flag(client):
    res = login(client, "intern", "welcome123")
    assert res.status_code == 200
    assert b"Welcome, Ira Intern" in res.data
    assert FLAG.encode() not in res.data


def test_invalid_credentials_do_not_authenticate(client):
    res = client.post("/login", data={"username": "intern", "password": "wrong"})
    assert res.status_code == 401
    assert b"Invalid username or password" in res.data
    assert client.get("/dashboard").status_code == 302


@pytest.mark.parametrize("user,pw", [("admin' --", "x"), ("' OR '1'='1' --", "x"), ("x", "' OR '1'='1")])
def test_intended_sql_injection_bypass_shows_flag(client, user, pw):
    res = login(client, user, pw)
    assert res.status_code == 200
    assert FLAG.encode() in res.data


def test_dashboard_requires_session(client):
    res = client.get("/dashboard")
    assert res.status_code == 302 and "/login" in res.headers["Location"]


def test_logout_invalidates_session(client):
    login(client, "admin' --", "x")
    assert client.get("/dashboard").status_code == 200
    client.get("/logout")
    assert client.get("/dashboard").status_code == 302


def test_flag_never_shown_before_bypass(client):
    assert FLAG.encode() not in client.get("/").data
    assert FLAG.encode() not in client.get("/dashboard", follow_redirects=True).data
    assert FLAG.encode() not in client.post("/login", data={"username": "a", "password": "b"}).data


def test_destructive_sql_is_blocked_and_db_intact(client):
    res = client.post("/login", data={"username": "x'; DROP TABLE users; --", "password": "x"})
    assert res.status_code in (400, 401)
    assert b"Welcome, Ira Intern" in login(client, "intern", "welcome123").data


def test_custom_404(client):
    res = client.get("/nope")
    assert res.status_code == 404 and b"Page not found" in res.data
