# veljkoloncarevic.in.rs — Flask + SQLite rebuild

Server-rendered rebuild of the static resume site. Same visual design, fluid/responsive
layout, all content in SQLite, private admin for CRUD, Docker-ready.

## Stack

| Piece | Choice | Why |
|---|---|---|
| Framework | Flask 3 + Jinja2 | Server-side HTML on first response — no JS needed to index |
| Data | SQLite (stdlib `sqlite3`, WAL) | Single-writer site; no ORM overhead for 4 tables |
| Auth | Flask session cookie + `werkzeug` hashes + CSRF tokens | Only you use `/admin` |
| Server | gunicorn, 1 worker / 8 threads | SQLite writes serialise anyway |
| Uploads | Filesystem under `/data/uploads`, served by Flask | Keeps the DB small and backups trivial |

## Layout

```
app/
  __init__.py      app factory, config, security headers
  db.py            connection, queries, CLI (init-db / seed-db / create-admin)
  schema.sql       users, profile, pages, sections, section_items
  seed.py          current live-site content as starting data
  auth.py          login/logout, @login_required, CSRF
  public.py        /, /<slug>, /uploads/<file>, /robots.txt, /sitemap.xml
  admin.py         CRUD for profile, pages, sections, items + reordering
  templates/       base.html, public/*, admin/*
  static/css       style.css (public), admin.css
  static/js        site.js (mobile nav toggle only)
wsgi.py            entry point
Dockerfile, docker-compose.yml, .env.example
```

## Data model

- **profile** — single row (id = 1): hero text, contact bar, portrait, PDF. `birthdate` is
  stored and **age is computed at render**, so "Veljko Lončarević, 24" never goes stale.
- **pages** — `/` (home), `/resume`, `/literature`, plus anything you add. Each carries its
  own `<title>` and meta description.
- **sections** — belong to a page; have `col` (`left` / `right` / `full`), `layout`, and
  `sort_order`.
- **section_items** — the cards. Layouts:
  - `timeline` — logo, title, org, description, dates (Work Experience, Internships, Education)
  - `publications` — consecutive items sharing a `group_label` render under one header with
    one conference logo, matching the current IcETRAN / TIE / Infoteh grouping
  - `text` — free paragraphs
  - `poems` — verse: hard line breaks, the blank line between stanzas and any leading
    indentation survive (`white-space: pre-wrap`); `title` is the poem title, `description`
    the verse, `subtitle` an optional dedication, `date_text` e.g. the year
  - `tags` — pill list for skills/tools

## Run it locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export COOKIE_SECURE=0          # plain http on localhost

flask --app wsgi seed-db        # creates tables + loads current site content
flask --app wsgi create-admin   # prompts for username/password (min 12 chars)
flask --app wsgi run --debug    # http://127.0.0.1:5000
```

Then open `/admin`, go to **Profile**, and upload your portrait, the resume PDF, and the
company/conference logos — the seed intentionally leaves image paths empty.

## Run it in Docker

```bash
cp .env.example .env            # set SECRET_KEY and SITE_URL
docker compose up -d --build

docker compose exec web flask --app wsgi seed-db
docker compose exec web flask --app wsgi create-admin
```

Content and uploads live in the `site-data` volume, so rebuilds don't touch your data.
Back up with:

```bash
docker compose exec web sqlite3 /data/site.db ".backup '/data/backup.db'"
docker compose cp web:/data/backup.db ./backup.db
```

(`sqlite3` CLI isn't in the slim image — either `apt-get install sqlite3` in the Dockerfile
or just `docker compose cp web:/data ./data-backup` while the app is idle.)

Put Caddy or nginx in front for TLS and proxy to `web:8000`. Keep `COOKIE_SECURE=1` there.

## Responsiveness

The original layout was desktop-locked. This rebuild is fluid-first:

- Type and spacing scale with `clamp()` — no fixed px sizes in the shell.
- Two-column grid collapses to one at **1100px**.
- At **720px**: hamburger nav, stacked hero (photo above text), contact bar goes vertical,
  justified text switches to ragged-right so narrow columns don't get rivers.
- At **420px**: logos stack above entry text.
- Print stylesheet keeps the two-column resume and drops the nav.
- `prefers-reduced-motion` respected; skip link and visible focus rings for keyboard use.

## SEO

- Full HTML on first response — nothing renders client-side.
- Per-page `<title>`, meta description, canonical, Open Graph, Twitter card.
- JSON-LD: `Person` for the profile, plus a `ScholarlyArticle` per publication with
  `isPartOf` pointing at the conference — Google reads your papers as structured records.
- `/sitemap.xml` generated from the `pages` table, `/robots.txt` disallows `/admin`.
- Real `<h1>`/`<h2>`/`<h3>` hierarchy, `loading="lazy"` on logos, width/height on images
  to avoid layout shift.

## Security notes

- Admin behind session auth; `/admin` is `noindex, nofollow` and disallowed in robots.txt.
- CSRF token on every POST, including deletes.
- Uploads: extension allowlist, `secure_filename`, random suffix, 8 MB cap.
- Cookies `HttpOnly` + `SameSite=Lax` + `Secure` in production.
- In-process failed-login counter (10 attempts) — restart clears it. If the site ever gets
  real traffic, move this to fail2ban or a reverse-proxy rate limit.
- `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` set on every response.

## Not done / next steps

- Font Awesome loads from a CDN (as before). Self-host it if you want zero third-party calls.
- Reordering is ↑/↓ buttons, not drag-and-drop — no JS dependency, works on mobile.
- No image resizing on upload; Pillow + a thumbnail step would help if you upload large logos.
