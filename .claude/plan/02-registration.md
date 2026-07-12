# Plan: Step 2 — Registration

## Context

The `register.html` form already exists and POSTs to `/register`, but `app.py` only handled `GET /register`. This step adds the `POST` handler so users can actually create accounts.

All validation, password hashing, and DB insertion happen inside the single `/register` route function.

---

## Files changed

| File | What changed |
|---|---|
| `expense-tracker/app.py` | Merged GET + POST into one `/register` route; added imports |

No new files, no schema changes, no new packages.

---

## Imports added in `app.py`

```python
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
from database.db import get_db, init_db, close_db, seed_db
```

---

## Route implementation

```python
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not name or not email or not password:
            return render_template("register.html", error="All fields are required.")
        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters.")

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return render_template("register.html", error="An account with that email already exists.")

        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password))
        )
        db.commit()
        return redirect(url_for("login"))

    return render_template("register.html")
```

---

## Validation rules (in order)

| Check | Error shown |
|---|---|
| Any field empty after strip | `"All fields are required."` |
| `password` length < 8 | `"Password must be at least 8 characters."` |
| Email already in `users` | `"An account with that email already exists."` |

---

## Verification

1. Start the app: `python app.py` (from `expense-tracker/`)
2. Open `http://127.0.0.1:5001/register`
3. Submit with all fields empty → error: *"All fields are required."*
4. Submit with password `abc1234` (7 chars) → error: *"Password must be at least 8 characters."*
5. Submit `demo@spendly.in` (already seeded) → error: *"An account with that email already exists."*
6. Submit a fresh email + password ≥ 8 chars → redirected to `/login`
7. Verify in DB: new user row appears with hashed (not plain-text) password.

---

## Definition of Done

- [x] `GET /register` still renders the form correctly
- [x] Submitting valid data creates a user in `users` with a hashed password
- [x] Submitting empty fields shows `"All fields are required."`
- [x] Submitting a short password shows `"Password must be at least 8 characters."`
- [x] Submitting a duplicate email shows `"An account with that email already exists."`
- [x] Successful registration redirects to `/login`
- [x] Password is stored as a hash, never plain text
- [x] All SQL uses parameterized queries
