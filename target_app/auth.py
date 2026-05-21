"""Authentication logic — register, login, logout, session check."""

from db import query_user, create_user, create_session, get_session, delete_session, log_action
from utils import hash_password, verify_password, generate_token, is_valid_username, sanitize_input


def register(username, password, email=None):
    """Register a new user. Returns (success: bool, message: str)."""
    username = sanitize_input(username)
    password = sanitize_input(password)

    if not is_valid_username(username):
        return False, "Invalid username (3-30 alphanumeric chars)"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if query_user(username):
        return False, "Username already taken"

    pw_hash = hash_password(password)
    user_id = create_user(username, pw_hash, email)
    log_action(user_id, "register")
    return True, "Registration successful"


def login(username, password):
    """Authenticate and return a session token. Returns (token|None, message)."""
    username = sanitize_input(username)
    user = query_user(username)
    if not user:
        return None, "Invalid credentials"

    if not verify_password(password, user["password_hash"]):
        log_action(user["id"], "failed_login")
        return None, "Invalid credentials"

    token = generate_token()
    create_session(token, user["id"])
    log_action(user["id"], "login")
    return token, "Login successful"


def logout(token):
    """Invalidate a session token."""
    session = get_session(token)
    if session:
        log_action(session["user_id"], "logout")
        delete_session(token)
        return True, "Logged out"
    return False, "Invalid session"


def get_current_user(token):
    """Return the user row for a valid session, or None."""
    if not token:
        return None
    session = get_session(token)
    if not session:
        return None
    from db import get_connection
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    conn.close()
    return user
