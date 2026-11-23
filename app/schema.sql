-- veljkoloncarevic.in.rs — content schema
-- SQLite. Run via `flask --app wsgi init-db`.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Single-row table (id = 1) holding the hero / contact bar content.
CREATE TABLE IF NOT EXISTS profile (
    id             INTEGER PRIMARY KEY CHECK (id = 1),
    full_name      TEXT NOT NULL,
    headline       TEXT,
    birthdate      TEXT,            -- ISO yyyy-mm-dd; age is computed, never stored
    bio            TEXT,
    email          TEXT,
    phone          TEXT,
    location       TEXT,
    github_label   TEXT,
    github_url     TEXT,
    linkedin_label TEXT,
    linkedin_url   TEXT,
    photo_path     TEXT,
    pdf_path       TEXT,
    updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    slug             TEXT NOT NULL UNIQUE,   -- '' = site root
    title            TEXT NOT NULL,
    meta_description TEXT,
    nav_label        TEXT,
    nav_icon         TEXT,                   -- font-awesome class, e.g. 'fa-file-lines'
    show_hero        INTEGER NOT NULL DEFAULT 1,
    sort_order       INTEGER NOT NULL DEFAULT 0,
    is_visible       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sections (
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
);

CREATE TABLE IF NOT EXISTS section_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id      INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    subtitle        TEXT,            -- role / organisation second line
    org             TEXT,            -- underlined org name next to subtitle
    description     TEXT,
    date_text       TEXT,            -- free text: 'October 2023 - present'
    badge           TEXT,            -- e.g. 'Published (M33)'
    link_url        TEXT,
    logo_path       TEXT,
    group_label     TEXT,            -- 'IcETRAN 2025 — Cacak | IEEE'
    group_logo_path TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    is_visible      INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_sections_page  ON sections(page_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_items_section  ON section_items(section_id, sort_order);
