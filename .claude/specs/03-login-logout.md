# Spec — Step 3: Login & Logout

## 1. Overview

Implement `POST /login` and `GET /logout` in `app.py`.

`POST /login` checks the user's credentials, writes the user's id into the Flask session, and redirects to a protected page. `GET /logout` clears the session and redirects to the landing page.

---

## 2. Depends on

- **Step 1 (Database)** — `get_db()` and the `users` table must exist.
- **Step 2 (Registration)** — users must already be stored with hashed passwords.

---

## 3. Routes

### A. `GET /login`

Already implemented — renders `login.html` with no error. Change its `methods` to accept `POST` too.

### B. `POST /login` *(new)*

| Item | Detail |
| --- | --- |
| URL | `/login` |
| Methods | `GET`, `POST` |
| Form fields | `email`, `password` |
| Success | Redirect to `GET /profile` |
| Failure | Re-render `login.html` with `error=` message |

### C. `GET /logout` *(replace stub)*

| Item | Detail |
| --- | --- |
| URL | `/logout` |
| Methods | `GET` |
| Success | Redirect to `GET /` (landing) |

---

## 4. Database

No schema changes — reads from the `users` table created in Step 1.

---

## 5. Logic for `POST /login`

1. Read `email` and `password` from `request.form` (strip whitespace).
2. Validate — both fields non-empty → error: `"Email and password are required."`
3. Look up the user: `SELECT id, password_hash FROM users WHERE email = ?`
4. If no row found → error: `"Invalid email or password."`
5. Call `check_password_hash(row['password_hash'], password)`.
6. If hash does not match → error: `"Invalid email or password."` *(same message — do not reveal which field is wrong)*
7. Write `session['user_id'] = row['id']`.
8. Redirect to `url_for('profile')`.

---

## 6. Logic for `GET /logout`

1. Call `session.clear()`.
2. Redirect to `url_for('landing')`.

---

## 7. Changes to `app.py`

- Add `session` to the Flask import line:
  ```python
  from flask import Flask, render_template, request, redirect, url_for, session
  ```
- Add import:
  ```python
  from werkzeug.security import generate_password_hash, check_password_hash
  ```
- Update `/login` route: change `methods` to `["GET", "POST"]`, add `POST` branch.
- Replace `/logout` stub with a real handler.

---

## 8. Files to Change

- `expense-tracker/app.py` — update `/login` and `/logout` routes

---

## 9. Files to Create

- None

---

## 10. Dependencies

No new pip packages. Uses:
- `werkzeug.security.check_password_hash` (already installed)
- `flask.session` (built-in; requires `app.secret_key` — already set)

---

## 11. Validation Rules

| Field | Rule | Error message |
| --- | --- | --- |
| email | Non-empty after strip | `"Email and password are required."` |
| password | Non-empty after strip | `"Email and password are required."` |
| email + password | Credential check passes | `"Invalid email or password."` |

---

## 12. Rules for Implementation

- Use `request.method == "POST"` to branch inside `/login`.
- Use parameterized queries only — no f-strings in SQL.
- Use `check_password_hash` — never compare plain-text passwords.
- On any validation failure, `render_template("login.html", error="...")` — do not redirect.
- Never reveal whether the email or the password was wrong — use the same generic message for both.
- On successful login, `redirect(url_for('profile'))`.
- `session.clear()` in logout clears all session keys at once — do not pop individual keys.

---

## 13. Expected Behavior

- `GET /login` renders the form as before.
- Submitting with empty fields → form re-renders with error, no session written.
- Submitting an unknown email → form re-renders with `"Invalid email or password."`, no session written.
- Submitting a wrong password → form re-renders with `"Invalid email or password."`, no session written.
- Submitting valid credentials → `session['user_id']` is set, redirect to `/profile`.
- Visiting `/logout` → session is cleared, redirect to `/`.

---

## 14. Error Handling Expectations

- Credential failures are handled by explicit checks (not by catching DB exceptions).
- DB errors bubble up naturally — do not swallow them.

---

## 15. Definition of Done

- [ ] `GET /login` still renders the form correctly
- [ ] Submitting empty fields shows `"Email and password are required."`
- [ ] Submitting an unknown email shows `"Invalid email or password."`
- [ ] Submitting a wrong password shows `"Invalid email or password."`
- [ ] Successful login writes `session['user_id']` and redirects to `/profile`
- [ ] `GET /logout` clears the session and redirects to `/`
- [ ] Passwords are never compared as plain text
- [ ] All SQL uses parameterized queries
