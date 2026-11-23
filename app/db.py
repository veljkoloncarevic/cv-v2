"""SQLite access layer. Plain sqlite3 — no ORM, the schema is small and stable."""
import os
import sqlite3
from datetime import date, datetime

import click
from flask import current_app, g
from werkzeug.security import generate_password_hash


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        # WAL keeps reads non-blocking while the admin writes.
        g.db.execute("PRAGMA journal_mode = WAL")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    lastrow = cur.lastrowid
    cur.close()
    return lastrow


# --------------------------------------------------------------------------
# Content readers used by the public (server-rendered) views
# --------------------------------------------------------------------------

def get_profile():
    return query("SELECT * FROM profile WHERE id = 1", one=True)


def compute_age(birthdate: str | None):
    if not birthdate:
        return None
    try:
        b = datetime.strptime(birthdate, "%Y-%m-%d").date()
    except ValueError:
        return None
    today = date.today()
    return today.year - b.year - ((today.month, today.day) < (b.month, b.day))


def get_pages(visible_only=True):
    sql = "SELECT * FROM pages"
    if visible_only:
        sql += " WHERE is_visible = 1"
    sql += " ORDER BY sort_order, id"
    return query(sql)


def get_page(slug, visible_only=True):
    sql = "SELECT * FROM pages WHERE slug = ?"
    if visible_only:
        sql += " AND is_visible = 1"
    return query(sql, (slug,), one=True)


def get_page_content(page_id, visible_only=True):
    """Return sections for a page, each with its items attached, in render order."""
    svis = " AND is_visible = 1" if visible_only else ""
    sections = query(
        f"SELECT * FROM sections WHERE page_id = ?{svis} ORDER BY sort_order, id",
        (page_id,),
    )
    out = []
    for s in sections:
        items = query(
            f"SELECT * FROM section_items WHERE section_id = ?{svis} "
            "ORDER BY sort_order, id",
            (s["id"],),
        )
        out.append({"section": s, "items": items})
    return out


def split_columns(blocks):
    """Split section blocks into (left, right, full) buckets for the desktop grid."""
    left = [b for b in blocks if b["section"]["col"] == "left"]
    right = [b for b in blocks if b["section"]["col"] == "right"]
    full = [b for b in blocks if b["section"]["col"] == "full"]
    return left, right, full


def group_items(items):
    """Collapse consecutive items sharing a group_label into one rendered header."""
    groups, current = [], None
    for it in items:
        label = it["group_label"] or ""
        if current is None or current["label"] != label:
            current = {
                "label": label,
                "logo": it["group_logo_path"],
                "items": [],
            }
            groups.append(current)
        if not current["logo"] and it["group_logo_path"]:
            current["logo"] = it["group_logo_path"]
        current["items"].append(it)
    return groups


def next_sort_order(table, fk_col, fk_id):
    row = query(
        f"SELECT COALESCE(MAX(sort_order), 0) + 10 AS n FROM {table} WHERE {fk_col} = ?",
        (fk_id,),
        one=True,
    )
    return row["n"]


def last_content_change():
    """Newest timestamp we can honestly report to Google in <lastmod>."""
    row = query("SELECT updated_at FROM profile WHERE id = 1", one=True)
    return (row["updated_at"] if row else None) or datetime.utcnow().isoformat()


# --------------------------------------------------------------------------
# Schema migrations
# --------------------------------------------------------------------------

# Keep in sync with the `sections` definition in schema.sql. It is duplicated
# because SQLite cannot widen a CHECK constraint in place — the only supported
# route is create-copy-drop-rename, which needs the full column list.
_SECTIONS_DDL = """
CREATE TABLE {table} (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id    INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    slug       TEXT NOT NULL,
    title      TEXT NOT NULL,
    subtitle   TEXT,
    col        TEXT NOT NULL DEFAULT 'left' CHECK (col IN ('left', 'right', 'full')),
    layout     TEXT NOT NULL DEFAULT 'timeline'
               CHECK (layout IN ('timeline', 'publications', 'text', 'tags', 'poems')),
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_visible INTEGER NOT NULL DEFAULT 1,
    UNIQUE (page_id, slug)
)
"""


def _sections_create_sql():
    row = query(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'sections'",
        one=True,
    )
    return (row[0] if row else "") or ""


def migrate_sections_layout():
    """Widen the `layout` CHECK to include 'poems' on databases created before
    that layout existed. A no-op on fresh or already-migrated databases.

    Row ids are preserved verbatim because section_items references them; the
    rebuild runs inside one transaction, with foreign keys suspended so the
    brief absence of the parent table cannot cascade-delete the children.
    Returns True when a rebuild actually happened.
    """
    if "'poems'" in _sections_create_sql():
        return False

    db = get_db()
    db.commit()  # PRAGMA foreign_keys is ignored inside a transaction
    db.execute("PRAGMA foreign_keys = OFF")
    try:
        db.executescript(
            "BEGIN;\n"
            + _SECTIONS_DDL.format(table="sections_rebuilt")
            + ";\n"
            "INSERT INTO sections_rebuilt (id, page_id, slug, title, subtitle,\n"
            "                              col, layout, sort_order, is_visible)\n"
            "     SELECT id, page_id, slug, title, subtitle, col,\n"
            "            layout, sort_order, is_visible FROM sections;\n"
            "DROP TABLE sections;\n"
            "ALTER TABLE sections_rebuilt RENAME TO sections;\n"
            "CREATE INDEX IF NOT EXISTS idx_sections_page\n"
            "    ON sections(page_id, sort_order);\n"
            "COMMIT;\n"
        )
    finally:
        db.execute("PRAGMA foreign_keys = ON")

    # A rename normally carries sqlite_sequence along; make sure the
    # AUTOINCREMENT counter still belongs to `sections` so new rows never
    # collide with migrated ids.
    db.execute("UPDATE sqlite_sequence SET name = 'sections' WHERE name = 'sections_rebuilt'")

    broken = db.execute("PRAGMA foreign_key_check").fetchall()
    if broken:
        raise RuntimeError(f"section layout migration broke references: {broken}")
    db.commit()
    return True


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def init_db():
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))
    db.commit()
    # Bring databases created before the `poems` layout up to date (no-op once done).
    if migrate_sections_layout():
        current_app.logger.info("Migrated sections.layout: added the 'poems' layout.")


@click.command("init-db")
def init_db_command():
    """Create tables (idempotent)."""
    init_db()
    click.echo(f"Initialised {current_app.config['DATABASE']}")


@click.command("seed-db")
def seed_db_command():
    """Load the current site content as starting data."""
    from .seed import seed

    init_db()
    seed()
    click.echo("Seeded content.")


@click.command("create-admin")
@click.option("--username", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
def create_admin_command(username, password):
    """Create or reset an admin user."""
    if len(password) < 12:
        raise click.ClickException("Use at least 12 characters.")
    init_db()
    execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?) "
        "ON CONFLICT(username) DO UPDATE SET password_hash = excluded.password_hash",
        (username, generate_password_hash(password)),
    )
    click.echo(f"Admin '{username}' ready.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_db_command)
    app.cli.add_command(create_admin_command)

    # Auto-create the schema on first boot so the container is self-starting.
    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
    with app.app_context():
        init_db()
