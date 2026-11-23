"""Private admin: CRUD for profile, pages, sections and section items."""
import os
import re
import secrets

from flask import (
    Blueprint, abort, current_app, flash, redirect, render_template, request,
    session, url_for,
)
from werkzeug.utils import secure_filename

from .auth import login_required
from .db import execute, get_pages, get_profile, next_sort_order, query

bp = Blueprint("admin", __name__, url_prefix="/admin")

ITEM_FIELDS = (
    "title", "subtitle", "org", "description", "date_text", "badge",
    "link_url", "group_label",
)


def _slugify(value, fallback="section"):
    s = re.sub(r"[^a-z0-9]+", "-", (value or "").lower().strip()).strip("-")
    return s or fallback


def _save_upload(field_name, existing=None):
    """Store an uploaded file under DATA_DIR/uploads and return its filename.
    Returns `existing` when nothing new was uploaded."""
    file = request.files.get(field_name)
    if not file or not file.filename:
        return existing

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in current_app.config["ALLOWED_UPLOAD_EXT"]:
        flash(f"Rejected {file.filename}: extension {ext or '(none)'} not allowed.", "error")
        return existing

    base = secure_filename(os.path.splitext(file.filename)[0])[:60] or "file"
    name = f"{base}-{secrets.token_hex(4)}{ext}"
    file.save(os.path.join(current_app.config["UPLOAD_DIR"], name))
    return name


def _delete_upload(filename):
    if not filename:
        return
    path = os.path.join(current_app.config["UPLOAD_DIR"], os.path.basename(filename))
    if os.path.isfile(path):
        os.remove(path)


def _form(name, default=""):
    return (request.form.get(name, default) or "").strip()


def _checkbox(name):
    return 1 if request.form.get(name) else 0


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------

@bp.route("/")
@login_required
def dashboard():
    pages = get_pages(visible_only=False)
    tree = []
    for p in pages:
        sections = query(
            "SELECT s.*, (SELECT COUNT(*) FROM section_items i WHERE i.section_id = s.id) "
            "AS item_count FROM sections s WHERE s.page_id = ? ORDER BY s.sort_order, s.id",
            (p["id"],),
        )
        tree.append({"page": p, "sections": sections})
    return render_template(
        "admin/dashboard.html", tree=tree, profile=get_profile(),
        username=session.get("username"),
    )


# --------------------------------------------------------------------------
# Profile (hero + contact bar)
# --------------------------------------------------------------------------

@bp.route("/profile", methods=("GET", "POST"))
@login_required
def profile_edit():
    profile = get_profile()
    if request.method == "POST":
        photo = _save_upload("photo", profile["photo_path"] if profile else None)
        pdf = _save_upload("pdf", profile["pdf_path"] if profile else None)
        execute(
            """INSERT INTO profile (id, full_name, headline, birthdate, bio, email,
                   phone, location, github_label, github_url, linkedin_label,
                   linkedin_url, photo_path, pdf_path, updated_at)
               VALUES (1,?,?,?,?,?,?,?,?,?,?,?,?,?, datetime('now'))
               ON CONFLICT(id) DO UPDATE SET
                   full_name=excluded.full_name, headline=excluded.headline,
                   birthdate=excluded.birthdate, bio=excluded.bio, email=excluded.email,
                   phone=excluded.phone, location=excluded.location,
                   github_label=excluded.github_label, github_url=excluded.github_url,
                   linkedin_label=excluded.linkedin_label,
                   linkedin_url=excluded.linkedin_url, photo_path=excluded.photo_path,
                   pdf_path=excluded.pdf_path, updated_at=datetime('now')""",
            (
                _form("full_name"), _form("headline"), _form("birthdate"), _form("bio"),
                _form("email"), _form("phone"), _form("location"),
                _form("github_label"), _form("github_url"),
                _form("linkedin_label"), _form("linkedin_url"), photo, pdf,
            ),
        )
        flash("Profile saved.", "ok")
        return redirect(url_for("admin.profile_edit"))
    return render_template("admin/profile.html", profile=profile)


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

@bp.route("/pages/new", methods=("GET", "POST"))
@bp.route("/pages/<int:page_id>/edit", methods=("GET", "POST"))
@login_required
def page_form(page_id=None):
    page = query("SELECT * FROM pages WHERE id = ?", (page_id,), one=True) if page_id else None
    if page_id and page is None:
        abort(404)

    if request.method == "POST":
        slug = _slugify(_form("slug") or _form("title"), fallback="")
        values = (
            slug, _form("title"), _form("meta_description"),
            _form("nav_label") or _form("title"), _form("nav_icon"),
            _checkbox("show_hero"), int(_form("sort_order", "0") or 0),
            _checkbox("is_visible"),
        )
        if page:
            execute(
                """UPDATE pages SET slug=?, title=?, meta_description=?, nav_label=?,
                   nav_icon=?, show_hero=?, sort_order=?, is_visible=? WHERE id=?""",
                values + (page["id"],),
            )
        else:
            page_id = execute(
                """INSERT INTO pages (slug, title, meta_description, nav_label,
                   nav_icon, show_hero, sort_order, is_visible)
                   VALUES (?,?,?,?,?,?,?,?)""",
                values,
            )
        flash("Page saved.", "ok")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/page_form.html", page=page)


@bp.post("/pages/<int:page_id>/delete")
@login_required
def page_delete(page_id):
    execute("DELETE FROM pages WHERE id = ?", (page_id,))   # cascades to sections/items
    flash("Page deleted.", "ok")
    return redirect(url_for("admin.dashboard"))


# --------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------

@bp.route("/pages/<int:page_id>/sections/new", methods=("GET", "POST"))
@bp.route("/sections/<int:section_id>/edit", methods=("GET", "POST"))
@login_required
def section_form(page_id=None, section_id=None):
    section = None
    if section_id:
        section = query("SELECT * FROM sections WHERE id = ?", (section_id,), one=True)
        if section is None:
            abort(404)
        page_id = section["page_id"]

    page = query("SELECT * FROM pages WHERE id = ?", (page_id,), one=True)
    if page is None:
        abort(404)

    if request.method == "POST":
        sort_order = _form("sort_order")
        values = (
            _slugify(_form("slug") or _form("title")), _form("title"), _form("subtitle"),
            _form("col", "left"), _form("layout", "timeline"),
            int(sort_order) if sort_order else next_sort_order("sections", "page_id", page_id),
            _checkbox("is_visible"),
        )
        if section:
            execute(
                """UPDATE sections SET slug=?, title=?, subtitle=?, col=?, layout=?,
                   sort_order=?, is_visible=? WHERE id=?""",
                values + (section["id"],),
            )
            section_id = section["id"]
        else:
            section_id = execute(
                """INSERT INTO sections (slug, title, subtitle, col, layout,
                   sort_order, is_visible, page_id) VALUES (?,?,?,?,?,?,?,?)""",
                values + (page_id,),
            )
        flash("Section saved.", "ok")
        return redirect(url_for("admin.section_items", section_id=section_id))

    return render_template("admin/section_form.html", section=section, page=page)


@bp.route("/sections/<int:section_id>/items")
@login_required
def section_items(section_id):
    section = query("SELECT * FROM sections WHERE id = ?", (section_id,), one=True)
    if section is None:
        abort(404)
    items = query(
        "SELECT * FROM section_items WHERE section_id = ? ORDER BY sort_order, id",
        (section_id,),
    )
    page = query("SELECT * FROM pages WHERE id = ?", (section["page_id"],), one=True)
    return render_template(
        "admin/section_items.html", section=section, items=items, page=page
    )


@bp.post("/sections/<int:section_id>/delete")
@login_required
def section_delete(section_id):
    for it in query("SELECT logo_path, group_logo_path FROM section_items WHERE section_id = ?",
                    (section_id,)):
        _delete_upload(it["logo_path"])
        _delete_upload(it["group_logo_path"])
    execute("DELETE FROM sections WHERE id = ?", (section_id,))
    flash("Section and its items deleted.", "ok")
    return redirect(url_for("admin.dashboard"))


@bp.post("/sections/<int:section_id>/move")
@login_required
def section_move(section_id):
    _move("sections", "page_id", section_id, request.form.get("dir", "up"))
    return redirect(url_for("admin.dashboard"))


# --------------------------------------------------------------------------
# Items
# --------------------------------------------------------------------------

@bp.route("/sections/<int:section_id>/items/new", methods=("GET", "POST"))
@bp.route("/items/<int:item_id>/edit", methods=("GET", "POST"))
@login_required
def item_form(section_id=None, item_id=None):
    item = None
    if item_id:
        item = query("SELECT * FROM section_items WHERE id = ?", (item_id,), one=True)
        if item is None:
            abort(404)
        section_id = item["section_id"]

    section = query("SELECT * FROM sections WHERE id = ?", (section_id,), one=True)
    if section is None:
        abort(404)

    if request.method == "POST":
        logo = _save_upload("logo", item["logo_path"] if item else None)
        group_logo = _save_upload("group_logo", item["group_logo_path"] if item else None)
        sort_order = _form("sort_order")
        values = tuple(_form(f) for f in ITEM_FIELDS) + (
            logo, group_logo,
            int(sort_order) if sort_order
            else next_sort_order("section_items", "section_id", section_id),
            _checkbox("is_visible"),
        )
        if item:
            execute(
                """UPDATE section_items SET title=?, subtitle=?, org=?, description=?,
                   date_text=?, badge=?, link_url=?, group_label=?, logo_path=?,
                   group_logo_path=?, sort_order=?, is_visible=? WHERE id=?""",
                values + (item["id"],),
            )
        else:
            execute(
                """INSERT INTO section_items (title, subtitle, org, description,
                   date_text, badge, link_url, group_label, logo_path, group_logo_path,
                   sort_order, is_visible, section_id)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                values + (section_id,),
            )
        flash("Item saved.", "ok")
        return redirect(url_for("admin.section_items", section_id=section_id))

    return render_template("admin/item_form.html", item=item, section=section)


@bp.post("/items/<int:item_id>/delete")
@login_required
def item_delete(item_id):
    item = query("SELECT * FROM section_items WHERE id = ?", (item_id,), one=True)
    if item is None:
        abort(404)
    _delete_upload(item["logo_path"])
    _delete_upload(item["group_logo_path"])
    execute("DELETE FROM section_items WHERE id = ?", (item_id,))
    flash("Item deleted.", "ok")
    return redirect(url_for("admin.section_items", section_id=item["section_id"]))


@bp.post("/items/<int:item_id>/move")
@login_required
def item_move(item_id):
    item = query("SELECT * FROM section_items WHERE id = ?", (item_id,), one=True)
    if item is None:
        abort(404)
    _move("section_items", "section_id", item_id, request.form.get("dir", "up"))
    return redirect(url_for("admin.section_items", section_id=item["section_id"]))


def _move(table, fk_col, row_id, direction):
    """Swap sort_order with the neighbouring row in the same parent."""
    row = query(f"SELECT * FROM {table} WHERE id = ?", (row_id,), one=True)
    if row is None:
        abort(404)
    op, order = ("<", "DESC") if direction == "up" else (">", "ASC")
    neighbour = query(
        f"SELECT * FROM {table} WHERE {fk_col} = ? AND "
        f"(sort_order {op} ? OR (sort_order = ? AND id {op} ?)) "
        f"ORDER BY sort_order {order}, id {order} LIMIT 1",
        (row[fk_col], row["sort_order"], row["sort_order"], row_id),
        one=True,
    )
    if neighbour is None:
        return
    execute(f"UPDATE {table} SET sort_order = ? WHERE id = ?",
            (neighbour["sort_order"], row_id))
    execute(f"UPDATE {table} SET sort_order = ? WHERE id = ?",
            (row["sort_order"], neighbour["id"]))
