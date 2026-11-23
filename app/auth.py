"""Session auth + CSRF for the private admin area."""
import functools
import hmac
import secrets

from flask import (
    Blueprint, abort, current_app, flash, g, redirect, render_template,
    request, session, url_for,
)
from werkzeug.security import check_password_hash

from .db import query

bp = Blueprint("auth", __name__, url_prefix="/admin")

# Very small brute-force damper: per-process counter, resets on restart.
_FAILURES: dict[str, int] = {}


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def verify_csrf():
    sent = request.form.get("_csrf", "")
    if not hmac.compare_digest(sent, session.get("_csrf", "")):
        abort(400, "CSRF token mismatch — reload the form and try again.")


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login", next=request.path))
        if request.method == "POST":
            verify_csrf()
        return view(*args, **kwargs)

    return wrapped


@bp.route("/login", methods=("GET", "POST"))
def login():
    if session.get("user_id"):
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        verify_csrf()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if _FAILURES.get(username, 0) >= 10:
            flash("Too many failed attempts. Restart the app to clear the lock.", "error")
            return render_template("admin/login.html", csrf=csrf_token())

        user = query("SELECT * FROM users WHERE username = ?", (username,), one=True)
        if user and check_password_hash(user["password_hash"], password):
            _FAILURES.pop(username, None)
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session.permanent = True
            nxt = request.args.get("next", "")
            # Only allow local redirects.
            return redirect(nxt if nxt.startswith("/") else url_for("admin.dashboard"))

        _FAILURES[username] = _FAILURES.get(username, 0) + 1
        flash("Invalid credentials.", "error")

    return render_template("admin/login.html", csrf=csrf_token())


@bp.post("/logout")
def logout():
    verify_csrf()
    session.clear()
    return redirect(url_for("auth.login"))


@bp.app_context_processor
def inject_csrf():
    return {"csrf_token": csrf_token}
