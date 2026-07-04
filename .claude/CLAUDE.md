# CLAUDE.md 

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**Spendly** is a Flask expense-tracker web app targeting INR (₹) expenses. The project is structured as a step-by-step student build — many routes and the database layer are stubs intentionally left for students to implement.

## Running the app

All commands run from the `expense-tracker/` subdirectory:

```bash
cd expense-tracker

# First-time setup
python -m venv ../venv
source ../venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt

# Run dev server (port 5001)
python app.py
```
## Code style
Python: PEP 8, snake_case for all variables and functions
Templates: Jinja2 with url_for() for every internal link — never hardcode URLs
Route functions: one responsibility only — fetch data, render template, done
DB queries: always use parameterized queries (? placeholders) — never f-strings in SQL
Error handling: use abort() for HTTP errors, not bare return "error string"

## Running tests

```bash
cd expense-tracker
pytest                        # all tests
pytest tests/test_auth.py     # single file (tests don't exist yet; add them here)
```

## Architecture

```
expense-tracker/
  app.py              # Flask app — all routes live here
  database/
    db.py             # get_db(), init_db(), seed_db() — stub; Step 1 to implement
  templates/
    base.html         # layout: navbar + main + footer; all pages extend this
    landing.html      # marketing page
    login.html        # POST /login (form submission; handler not yet implemented)
    register.html     # POST /register (form submission; handler not yet implemented)
    terms.html        # static legal page
    privacy.html      # static legal page
  static/
    css/style.css     # single CSS file — entire design system (no framework)
    js/main.js        # placeholder; JS added here as features are built
```

### Key conventions

**Routes** — `app.py` has two groups: implemented page renders at the top, and stub routes below marked `"coming in Step N"`. When implementing a stub, add the full handler where the stub is (don't create new files).

**Database** — SQLite, file `expense_tracker.db` (gitignored). The `database/db.py` module must expose `get_db()` returning a connection with `row_factory = sqlite3.Row` and `PRAGMA foreign_keys = ON`. Call `init_db()` once at startup.

**Templates** — all pages `{% extends "base.html" %}` and fill `{% block title %}` and `{% block content %}`. The base template loads Google Fonts (DM Serif Display + DM Sans) and the single stylesheet. An optional `{% block scripts %}` block exists for per-page JS.

**CSS design tokens** — colors, radii, and widths are all CSS custom properties defined in `:root` at the top of `style.css`. Use these variables rather than hard-coding values. The accent color is dark green (`--accent: #1a472a`).

**Auth pages** — `register.html` and `login.html` both accept an optional `error` template variable; render it with `render_template("register.html", error="...")` to show the `.auth-error` block.

## Planned step sequence (student build order)

1. Database setup — implement `database/db.py`
2. Registration — POST `/register` with password hashing
3. Login / logout — session management
4. Profile page
5–6. Expense list / dashboard
7–9. Add / edit / delete expense CRUD
