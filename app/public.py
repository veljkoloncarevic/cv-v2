"""Public, server-rendered views. Everything here returns complete HTML on first
response so Googlebot never needs to execute JavaScript."""
import json
import os

from flask import (
    Blueprint, Response, abort, current_app, render_template, send_from_directory,
    url_for,
)

from .db import (
    compute_age, get_page, get_page_content, get_pages, get_profile,
    group_items, last_content_change, split_columns,
)

bp = Blueprint("public", __name__)


def _person_jsonld(profile, age, blocks, site_url):
    """Person + ScholarlyArticle structured data — this is the SEO win over the
    current static page."""
    person = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": profile["full_name"],
        "url": site_url,
        "jobTitle": profile["headline"],
        "description": (profile["bio"] or "").strip(),
    }
    if profile["photo_path"]:
        person["image"] = site_url + url_for("public.upload", filename=profile["photo_path"])
    if profile["email"]:
        person["email"] = f"mailto:{profile['email']}"
    if profile["location"]:
        person["address"] = {"@type": "PostalAddress", "addressLocality": profile["location"]}
    sameas = [u for u in (profile["github_url"], profile["linkedin_url"]) if u]
    if sameas:
        person["sameAs"] = sameas

    docs = [person]
    for block in blocks:
        if block["section"]["layout"] != "publications":
            continue
        for it in block["items"]:
            article = {
                "@context": "https://schema.org",
                "@type": "ScholarlyArticle",
                "headline": it["title"],
                "author": {"@type": "Person", "name": profile["full_name"]},
            }
            if it["link_url"]:
                article["url"] = it["link_url"]
            if it["group_label"]:
                article["isPartOf"] = {"@type": "PublicationEvent", "name": it["group_label"]}
            if it["date_text"]:
                article["datePublished"] = it["date_text"]
            docs.append(article)
    return json.dumps(docs, ensure_ascii=False, indent=None)


def _render_page(page):
    profile = get_profile()
    if profile is None:
        abort(500, "Profile row missing — run `flask --app wsgi seed-db`.")

    blocks = get_page_content(page["id"])
    left, right, full = split_columns(blocks)
    site_url = current_app.config["SITE_URL"].rstrip("/")

    return render_template(
        "public/page.html",
        page=page,
        profile=profile,
        age=compute_age(profile["birthdate"]),
        nav_pages=get_pages(),
        left=left,
        right=right,
        full=full,
        group_items=group_items,
        canonical=site_url + url_for("public.page", slug=page["slug"]).rstrip("/"),
        jsonld=_person_jsonld(profile, compute_age(profile["birthdate"]), blocks, site_url),
    )


@bp.route("/")
@bp.route("/<path:slug>")
def page(slug=""):
    slug = slug.strip("/")
    page_row = get_page(slug)
    if page_row is None:
        abort(404)
    return _render_page(page_row)


@bp.route("/uploads/<path:filename>")
def upload(filename):
    return send_from_directory(
        current_app.config["UPLOAD_DIR"], filename, max_age=60 * 60 * 24 * 30
    )


@bp.route("/robots.txt")
def robots():
    site_url = current_app.config["SITE_URL"].rstrip("/")
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin\n"
        f"Sitemap: {site_url}/sitemap.xml\n"
    )
    return Response(body, mimetype="text/plain")


@bp.route("/sitemap.xml")
def sitemap():
    site_url = current_app.config["SITE_URL"].rstrip("/")
    lastmod = (last_content_change() or "")[:10]
    urls = []
    for p in get_pages():
        loc = site_url + url_for("public.page", slug=p["slug"])
        loc = loc.rstrip("/") or site_url
        urls.append(
            "  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <priority>{'1.0' if not p['slug'] else '0.8'}</priority>\n"
            "  </url>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    return Response(xml, mimetype="application/xml")


@bp.app_errorhandler(404)
def not_found(e):
    return render_template("public/404.html", nav_pages=get_pages()), 404
