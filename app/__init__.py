"""Application factory for veljkoloncarevic.in.rs."""
import os
from datetime import timedelta

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    # Behind Nginx Proxy Manager: trust forwarded headers from exactly one hop.
    # Without this Flask sees every request as plain http, so the Secure session
    # cookie never sticks and /admin login redirects loop.
    # Render NULL/None as empty string, never the literal "None".
    app.jinja_env.finalize = lambda v: "" if v is None else v
    if os.environ.get("TRUST_PROXY", "1") == "1":
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
        )
    data_dir = os.environ.get("DATA_DIR", os.path.join(app.root_path, "..", "data"))
    data_dir = os.path.abspath(data_dir)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.environ.get("DATABASE_PATH", os.path.join(data_dir, "site.db")),
        UPLOAD_DIR=os.environ.get("UPLOAD_DIR", os.path.join(data_dir, "uploads")),
        SITE_URL=os.environ.get("SITE_URL", "https://www.veljkoloncarevic.in.rs"),
        MAX_CONTENT_LENGTH=8 * 1024 * 1024,          # 8 MB upload ceiling
        ALLOWED_UPLOAD_EXT={".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".pdf"},
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "1") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)

    from . import db

    db.init_app(app)

    from . import admin, auth, public

    app.register_blueprint(public.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return resp

    return app
