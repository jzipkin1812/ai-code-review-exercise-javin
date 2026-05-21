"""Basic tests for the Flask user-login app."""

import sys, os, tempfile, pytest

# Allow imports from parent directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    os.environ["APP_DB_PATH"] = db_path
    from db import init_db
    init_db()
    yield
    os.environ.pop("APP_DB_PATH", None)


@pytest.fixture
def client():
    from app import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_register_and_login(client):
    r = client.post("/register", json={
        "username": "alice", "password": "secret123"
    })
    assert r.status_code == 201

    r = client.post("/login", json={
        "username": "alice", "password": "secret123"
    })
    assert r.status_code == 200
    assert r.get_json()["ok"] is True


def test_register_duplicate(client):
    client.post("/register", json={
        "username": "bob", "password": "pass1234"
    })
    r = client.post("/register", json={
        "username": "bob", "password": "pass1234"
    })
    assert r.status_code == 400


def test_login_wrong_password(client):
    client.post("/register", json={
        "username": "carol", "password": "correct"
    })
    r = client.post("/login", json={
        "username": "carol", "password": "wrong"
    })
    assert r.status_code == 401


def test_me_unauthenticated(client):
    r = client.get("/me")
    assert r.status_code == 401
