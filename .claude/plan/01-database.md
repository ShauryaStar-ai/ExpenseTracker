# Plan: Step 1 — Database Setup

## Context

Spendly's `database/db.py` is a stub with zero executable code. Without it, no future step (auth, expenses, profile) can function. This plan implements the three required functions (`get_db`, `init_db`, `seed_db`) and wires the module into `app.py`.

---

## Files to change

| File | What changes |
|---|---|
| `expense-tracker/database/db.py` | Full implementation of `get_db`, `init_db`, `seed_db`, `close_db` |
| `expense-tracker/app.py` | Import db module, add `secret_key`, `DATABASE` config, teardown, `init_db()` call |

---

## Schema

### `users`
| Column | Type | Constraint |
|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` |
| `name` | `TEXT` | `NOT NULL` |
| `email` | `TEXT` | `NOT NULL UNIQUE` |
| `password_hash` | `TEXT` | `NOT NULL` |
| `created_at` | `TEXT` | `NOT NULL DEFAULT (datetime('now'))` |

### `expenses`
| Column | Type | Constraint |
|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` |
| `user_id` | `INTEGER` | `NOT NULL REFERENCES users(id) ON DELETE CASCADE` |
| `amount` | `REAL` | `NOT NULL` |
| `category` | `TEXT` | `NOT NULL` |
| `date` | `TEXT` | `NOT NULL` (ISO-8601 `YYYY-MM-DD`) |
| `description` | `TEXT` | nullable |
| `created_at` | `TEXT` | `NOT NULL DEFAULT (datetime('now'))` |

---

## `database/db.py` — full implementation

```python
import sqlite3
import os
from flask import g, current_app


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            email         TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            amount      REAL NOT NULL,
            category    TEXT NOT NULL,
            date        TEXT NOT NULL,
            description TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
    ''')
    db.commit()


def seed_db():
    from werkzeug.security import generate_password_hash
    db = get_db()
    db.execute(
        'INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        ('Demo User', 'demo@spendly.in', generate_password_hash('password123'))
    )
    db.commit()
    user = db.execute(
        'SELECT id FROM users WHERE email = ?', ('demo@spendly.in',)
    ).fetchone()
    if user:
        db.executemany(
            'INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)',
            [
                (user['id'], 450.00,  'Food',   '2026-06-28', 'Groceries'),
                (user['id'], 1200.00, 'Travel', '2026-06-25', 'Auto to office'),
                (user['id'], 800.00,  'Bills',  '2026-07-01', 'Electricity bill'),
            ]
        )
        db.commit()
```

---

## `app.py` — changes

**Imports to add at the top:**
```python
import os
from database.db import init_db, close_db
```

**After `app = Flask(__name__)`, add:**
```python
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
app.config['DATABASE'] = os.path.join(app.root_path, 'expense_tracker.db')
app.teardown_appcontext(close_db)
```

**In `if __name__ == "__main__":` block:**
```python
if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True, port=5001)
```

---

## Verification

1. `cd expense-tracker && python app.py` — server starts with no errors; `expense_tracker.db` is created.
2. Check tables exist:
   ```bash
   python -c "import sqlite3; c=sqlite3.connect('expense_tracker.db'); print([r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")])"
   ```
   Expected output: `['users', 'expenses']`
3. Navigate to `http://127.0.0.1:5001/` — landing page still loads (no regressions).
