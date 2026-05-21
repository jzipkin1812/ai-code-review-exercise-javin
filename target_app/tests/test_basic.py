"""Tests for the Flask application."""

import sys, os, pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    os.environ["APP_DB_PATH"] = db_path
    os.environ["UPLOAD_FOLDER"] = str(tmp_path / "uploads")
    from db import init_db
    init_db()
    yield
    os.environ.pop("APP_DB_PATH", None)
    os.environ.pop("UPLOAD_FOLDER", None)


@pytest.fixture
def client():
    from app import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _register_and_login(client, username="alice", password="secret123"):
    client.post("/register", json={"username": username, "password": password})
    client.post("/login", json={"username": username, "password": password})


# ── Auth tests ───────────────────────────────────────────────

def test_health(client):
    assert client.get("/health").get_json()["status"] == "ok"


def test_register_and_login(client):
    r = client.post("/register", json={"username": "alice", "password": "secret123"})
    assert r.status_code == 201
    r = client.post("/login", json={"username": "alice", "password": "secret123"})
    assert r.status_code == 200


def test_register_duplicate(client):
    client.post("/register", json={"username": "bob", "password": "pass1234"})
    r = client.post("/register", json={"username": "bob", "password": "pass1234"})
    assert r.status_code == 400


def test_login_wrong_password(client):
    client.post("/register", json={"username": "carol", "password": "correct"})
    r = client.post("/login", json={"username": "carol", "password": "wrong"})
    assert r.status_code == 401


def test_me_unauthenticated(client):
    assert client.get("/me").status_code == 401


# ── Notes tests ──────────────────────────────────────────────

def test_create_and_list_notes(client):
    _register_and_login(client)
    r = client.post("/notes", json={"title": "My Note", "body": "Hello world"})
    assert r.status_code == 201
    note_id = r.get_json()["note_id"]
    r = client.get("/notes")
    assert r.status_code == 200
    assert len(r.get_json()["notes"]) == 1


def test_get_note(client):
    _register_and_login(client)
    r = client.post("/notes", json={"title": "Test", "body": "Content"})
    note_id = r.get_json()["note_id"]
    r = client.get(f"/notes/{note_id}")
    assert r.get_json()["note"]["title"] == "Test"


def test_delete_note(client):
    _register_and_login(client)
    r = client.post("/notes", json={"title": "ToDelete", "body": ""})
    note_id = r.get_json()["note_id"]
    r = client.delete(f"/notes/{note_id}")
    assert r.get_json()["ok"] is True
    r = client.get(f"/notes/{note_id}")
    assert r.status_code == 404


def test_notes_require_auth(client):
    assert client.get("/notes").status_code == 401
    assert client.post("/notes", json={"title": "X"}).status_code == 401


# ── Admin tests ──────────────────────────────────────────────

def test_admin_requires_admin_role(client):
    _register_and_login(client)
    assert client.get("/admin/users").status_code == 403


# ── API key tests ────────────────────────────────────────────

def test_create_api_key(client):
    _register_and_login(client)
    r = client.post("/api-keys")
    assert r.status_code == 201
    assert r.get_json()["api_key"].startswith("sk_")


# ── Search tests ─────────────────────────────────────────────

def test_search_notes(client):
    _register_and_login(client)
    client.post("/notes", json={"title": "Security Review", "body": "Found SQL injection"})
    client.post("/notes", json={"title": "Meeting Notes", "body": "Discuss budget"})
    r = client.get("/search/notes?q=security")
    assert len(r.get_json()["results"]) == 1
