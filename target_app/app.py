"""Flask user-login application — the codebase that PRs target."""

from flask import Flask, request, jsonify, g
from db import init_db
from auth import register, login, logout, get_current_user

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me-in-production"


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


# ── Authenticated endpoints ──────────────────────────────────

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


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ── Entry point ──────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
