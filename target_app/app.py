"""Flask application — user accounts, notes, file uploads, admin panel."""

import os
from flask import Flask, request, jsonify, g, send_from_directory
from db import init_db
from auth import register, login, logout, get_current_user

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-in-production")
app.config["UPLOAD_FOLDER"] = os.environ.get("UPLOAD_FOLDER", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB


@app.before_request
def load_user():
    """Attach the current user to g if a session token is present."""
    token = request.cookies.get("session_token")
    g.user = get_current_user(token)


# ── Public endpoints ─────────────────────────────────────────

@app.route("/register", methods=["POST"])
def register_endpoint():
    data = request.get_json(force=True)
    ok, msg = register(data.get("username", ""), data.get("password", ""),
                       data.get("email"))
    status = 201 if ok else 400
    return jsonify({"ok": ok, "message": msg}), status


@app.route("/login", methods=["POST"])
def login_endpoint():
    data = request.get_json(force=True)
    token, msg = login(data.get("username", ""), data.get("password", ""))
    if token:
        resp = jsonify({"ok": True, "message": msg})
        resp.set_cookie("session_token", token, httponly=True, samesite="Lax")
        return resp
    return jsonify({"ok": False, "message": msg}), 401


@app.route("/logout", methods=["POST"])
def logout_endpoint():
    token = request.cookies.get("session_token")
    ok, msg = logout(token)
    resp = jsonify({"ok": ok, "message": msg})
    if ok:
        resp.delete_cookie("session_token")
    return resp


@app.route("/me")
def me_endpoint():
    if not g.user:
        return jsonify({"ok": False, "message": "Not logged in"}), 401
    return jsonify({
        "ok": True,
        "user": {
            "id": g.user["id"],
            "username": g.user["username"],
            "email": g.user["email"],
            "role": g.user["role"],
        },
    })


# ── Notes (CRUD) ─────────────────────────────────────────────

@app.route("/notes", methods=["GET"])
def list_notes():
    if not g.user:
        return jsonify({"ok": False, "message": "Auth required"}), 401
    from db import get_connection
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, title, created_at FROM notes WHERE user_id = ? ORDER BY created_at DESC",
        (g.user["id"],)
    ).fetchall()
    conn.close()
    return jsonify({"ok": True, "notes": [dict(r) for r in rows]})


@app.route("/notes", methods=["POST"])
def create_note():
    if not g.user:
        return jsonify({"ok": False, "message": "Auth required"}), 401
    data = request.get_json(force=True)
    title = data.get("title", "").strip()[:200]
    body = data.get("body", "").strip()[:10000]
    if not title:
        return jsonify({"ok": False, "message": "Title required"}), 400
    from db import get_connection, log_action
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO notes (user_id, title, body) VALUES (?, ?, ?)",
        (g.user["id"], title, body)
    )
    conn.commit()
    note_id = cur.lastrowid
    conn.close()
    log_action(g.user["id"], "create_note", f"note_id={note_id}")
    return jsonify({"ok": True, "note_id": note_id}), 201


@app.route("/notes/<int:note_id>")
def get_note(note_id):
    if not g.user:
        return jsonify({"ok": False, "message": "Auth required"}), 401
    from db import get_connection
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM notes WHERE id = ? AND user_id = ?",
        (note_id, g.user["id"])
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"ok": False, "message": "Not found"}), 404
    return jsonify({"ok": True, "note": dict(row)})


@app.route("/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    if not g.user:
        return jsonify({"ok": False, "message": "Auth required"}), 401
    from db import get_connection, log_action
    conn = get_connection()
    conn.execute(
        "DELETE FROM notes WHERE id = ? AND user_id = ?",
        (note_id, g.user["id"])
    )
    conn.commit()
    conn.close()
    log_action(g.user["id"], "delete_note", f"note_id={note_id}")
    return jsonify({"ok": True, "message": "Deleted"})


# ── Note sharing ─────────────────────────────────────────────

@app.route("/notes/<int:note_id>/share", methods=["POST"])
def share_note(note_id):
    """Share a note with another user by username."""
    if not g.user:
        return jsonify({"ok": False, "message": "Auth required"}), 401
    data = request.get_json(force=True)
    target_user = data.get("username", "")
    from db import get_connection, query_user, log_action
    # Verify the note belongs to the current user
    conn = get_connection()
    note = conn.execute(
        "SELECT * FROM notes WHERE id = ? AND user_id = ?",
        (note_id, g.user["id"])
    ).fetchone()
    if not note:
        conn.close()
        return jsonify({"ok": False, "message": "Not found"}), 404
    target = query_user(target_user)
    if not target:
        conn.close()
        return jsonify({"ok": False, "message": "User not found"}), 404
    conn.execute(
        "INSERT OR IGNORE INTO shared_notes (note_id, shared_with_user_id) VALUES (?, ?)",
        (note_id, target["id"])
    )
    conn.commit()
    conn.close()
    log_action(g.user["id"], "share_note",
               f"note_id={note_id} shared_with={target_user}")
    return jsonify({"ok": True, "message": f"Shared with {target_user}"})


# ── File uploads ─────────────────────────────────────────────

ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "csv"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload", methods=["POST"])
def upload_file():
    if not g.user:
        return jsonify({"ok": False, "message": "Auth required"}), 401
    if "file" not in request.files:
        return jsonify({"ok": False, "message": "No file part"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"ok": False, "message": "No file selected"}), 400
    if not allowed_file(f.filename):
        return jsonify({"ok": False, "message": "File type not allowed"}), 400
    from werkzeug.utils import secure_filename
    from db import get_connection, log_action
    filename = secure_filename(f.filename)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    f.save(filepath)
    conn = get_connection()
    conn.execute(
        "INSERT INTO uploads (user_id, filename, filepath) VALUES (?, ?, ?)",
        (g.user["id"], filename, filepath)
    )
    conn.commit()
    conn.close()
    log_action(g.user["id"], "upload", f"file={filename}")
    return jsonify({"ok": True, "filename": filename}), 201


@app.route("/files/<filename>")
def serve_file(filename):
    if not g.user:
        return jsonify({"ok": False, "message": "Auth required"}), 401
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ── API keys ─────────────────────────────────────────────────

@app.route("/api-keys", methods=["POST"])
def create_api_key():
    """Generate a personal API key for programmatic access."""
    if not g.user:
        return jsonify({"ok": False, "message": "Auth required"}), 401
    from utils import generate_token
    from db import get_connection, log_action
    key = "sk_" + generate_token()[:32]
    conn = get_connection()
    conn.execute(
        "INSERT INTO api_keys (user_id, key_hash, prefix) VALUES (?, ?, ?)",
        (g.user["id"], key, key[:8])  # NOTE: storing full key as hash for simplicity
    )
    conn.commit()
    conn.close()
    log_action(g.user["id"], "create_api_key", f"prefix={key[:8]}")
    return jsonify({"ok": True, "api_key": key}), 201


@app.route("/api-keys", methods=["GET"])
def list_api_keys():
    if not g.user:
        return jsonify({"ok": False, "message": "Auth required"}), 401
    from db import get_connection
    conn = get_connection()
    rows = conn.execute(
        "SELECT prefix, created_at FROM api_keys WHERE user_id = ?",
        (g.user["id"],)
    ).fetchall()
    conn.close()
    return jsonify({"ok": True, "keys": [dict(r) for r in rows]})


# ── Admin panel ──────────────────────────────────────────────

@app.route("/admin/users")
def admin_list_users():
    """List all users (admin only)."""
    if not g.user or g.user["role"] != "admin":
        return jsonify({"ok": False, "message": "Admin required"}), 403
    from db import get_connection
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, username, email, role, created_at FROM users"
    ).fetchall()
    conn.close()
    return jsonify({"ok": True, "users": [dict(r) for r in rows]})


@app.route("/admin/users/<int:user_id>/role", methods=["PUT"])
def admin_set_role(user_id):
    """Change a user's role (admin only)."""
    if not g.user or g.user["role"] != "admin":
        return jsonify({"ok": False, "message": "Admin required"}), 403
    data = request.get_json(force=True)
    new_role = data.get("role", "")
    if new_role not in ("user", "admin", "moderator"):
        return jsonify({"ok": False, "message": "Invalid role"}), 400
    from db import get_connection, log_action
    conn = get_connection()
    conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    conn.close()
    log_action(g.user["id"], "set_role", f"user_id={user_id} role={new_role}")
    return jsonify({"ok": True, "message": f"Role updated to {new_role}"})


@app.route("/admin/audit")
def admin_audit_log():
    """View recent audit log entries (admin only)."""
    if not g.user or g.user["role"] != "admin":
        return jsonify({"ok": False, "message": "Admin required"}), 403
    from db import get_connection
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 100"
    ).fetchall()
    conn.close()
    return jsonify({"ok": True, "entries": [dict(r) for r in rows]})


# ── Misc ─────────────────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/search/notes")
def search_notes():
    """Search notes by keyword (authenticated users only)."""
    if not g.user:
        return jsonify({"ok": False, "message": "Auth required"}), 401
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify({"ok": False, "message": "Query too short"}), 400
    from db import get_connection
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, title, created_at FROM notes WHERE user_id = ? AND "
        "(title LIKE ? OR body LIKE ?) ORDER BY created_at DESC LIMIT 20",
        (g.user["id"], f"%{q}%", f"%{q}%")
    ).fetchall()
    conn.close()
    return jsonify({"ok": True, "results": [dict(r) for r in rows]})


# ── Entry point ──────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
