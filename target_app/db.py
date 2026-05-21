"""Database layer — SQLite with parameterized queries."""

import sqlite3
import os

DB_PATH = os.environ.get("APP_DB_PATH", "app.db")


def get_connection():
    """Return a new SQLite connection with row-factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            body TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shared_notes (
            note_id INTEGER NOT NULL,
            shared_with_user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (note_id, shared_with_user_id),
            FOREIGN KEY (note_id) REFERENCES notes(id),
            FOREIGN KEY (shared_with_user_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key_hash TEXT NOT NULL,
            prefix TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            detail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def query_user(username):
    """Look up a user by username (parameterized)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return row


def create_user(username, password_hash, email=None):
    """Insert a new user. Returns the new user id."""
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
        (username, password_hash, email),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id


def create_session(token, user_id):
    """Store a session token."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (token, user_id) VALUES (?, ?)",
        (token, user_id),
    )
    conn.commit()
    conn.close()


def get_session(token):
    """Look up a session by token."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM sessions WHERE token = ?", (token,)
    ).fetchone()
    conn.close()
    return row


def delete_session(token):
    """Remove a session token."""
    conn = get_connection()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def log_action(user_id, action, detail=None):
    """Write to the audit log."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_log (user_id, action, detail) VALUES (?, ?, ?)",
        (user_id, action, detail),
    )
    conn.commit()
    conn.close()
