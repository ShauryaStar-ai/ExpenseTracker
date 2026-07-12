# Spec Document

## 1. Overview

Implement the `POST /register` route in `app.py` so new users can create an account.

This step wires the existing `register.html` form to the database, validates input, hashes the password, inserts the user, and redirects to login on success.

---

## 2. Depends on

- **Step 1 (Database)** — `get_db()`, `init_db()`, and the `users` table must already exist.

---

## 3. Routes

### A. `GET /register`

Already implemented — renders `register.html` with no error.

### B. `POST /register` *(new)*

| Item | Detail |
| --- | --- |
| URL | `/register` |
| Methods | `GET`, `POST` |
| Form fields | `name`, `email`, `password` |
| Success | Redirect to `GET /login` |
| Failure | Re-render `register.html` with `error=` message |

---

## 4. Database

No schema changes — uses the `users` table created in Step 1.

---

## 5. Logic for `POST /register`

1. Read `name`, `email`, `password` from `request.form` (strip whitespace).
2. Validate:
   - All three fields must be non-empty → error: `"All fields are required."`
   - `password` must be at least 8 characters → error: `"Password must be at least 8 characters."`
3. Check if `email` already exists in `users` → error: `"An account with that email already exists."`
4. Hash the password using `werkzeug.security.generate_password_hash`.
5. Insert into `users` (name, email, password_hash).
6. Commit the connection.
7. Redirect to `url_for('login')`.

---

## 6. Changes to `app.py`

- Merge `GET` and `POST` into one route function with `methods=["GET", "POST"]`.
- Add imports:
  - `from flask import request, redirect, url_for` (add to existing Flask import line)
  - `from werkzeug.security import generate_password_hash`
  - `from database.db import get_db` (add to existing db import line)

---

## 7. Files to Change

- `expense-tracker/app.py` — update `/register` route

---

## 8. Files to Create

- None

---

## 9. Dependencies

No new pip packages. Uses:
- `werkzeug.security` (already installed)
- `sqlite3` via `get_db()` (already set up in Step 1)

---

## 10. Validation Rules

| Field | Rule | Error message |
| --- | --- | --- |
| name | Non-empty after strip | `"All fields are required."` |
| email | Non-empty after strip | `"All fields are required."` |
| password | Non-empty after strip | `"All fields are required."` |
| password | Length ≥ 4 | `"Password must be at least 4 characters."` |
| email | Not already in `users` | `"An account with that email already exists."` |

---

## 11. Rules for Implementation

- Use `request.method == "POST"` to branch inside the route.
- Use parameterized queries only — no f-strings in SQL.
- Never store plain-text passwords — always hash with `generate_password_hash`.
- On any validation failure, `render_template("register.html", error="...")` — do not redirect.
- On success, `redirect(url_for('login'))` — do not render a template.
- Use `abort()` for unexpected server errors, not bare string returns.

---

## 12. Expected Behavior

- Submitting the form with all valid fields → user is created, redirected to `/login`.
- Submitting with any empty field → form re-renders with error, no DB write.
- Submitting a password shorter than 8 chars → form re-renders with error, no DB write.
- Submitting a duplicate email → form re-renders with error, no DB write.
- Visiting `GET /register` still works as before.

---

## 13. Error Handling Expectations

- Duplicate email is caught by the pre-check query (before the INSERT), not by catching a database exception.
- DB errors bubble up naturally — do not swallow them.

---

## 14. Definition of Done

- [ ] `GET /register` still renders the form correctly
- [ ] Submitting valid data creates a user in `users` with a hashed password
- [ ] Submitting empty fields shows `"All fields are required."`
- [ ] Submitting a short password shows `"Password must be at least 8 characters."`
- [ ] Submitting a duplicate email shows `"An account with that email already exists."`
- [ ] Successful registration redirects to `/login`
- [ ] Password is stored as a hash, never plain text
- [ ] All SQL uses parameterized queries
