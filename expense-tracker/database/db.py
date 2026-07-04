import sqlite3
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
        existing = db.execute(
            'SELECT COUNT(*) FROM expenses WHERE user_id = ?', (user['id'],)
        ).fetchone()[0]
        if existing == 0:
            db.executemany(
                'INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)',
                [
                    (user['id'],  450.00, 'Food',          '2026-06-28', 'Groceries'),
                    (user['id'],  320.00, 'Food',          '2026-06-30', 'Restaurant lunch'),
                    (user['id'], 1200.00, 'Travel',        '2026-06-25', 'Auto to office'),
                    (user['id'], 2500.00, 'Travel',        '2026-06-22', 'Weekend trip'),
                    (user['id'],  800.00, 'Bills',         '2026-07-01', 'Electricity bill'),
                    (user['id'],  999.00, 'Shopping',      '2026-06-27', 'New shirt'),
                    (user['id'],  500.00, 'Entertainment', '2026-06-29', 'Movie tickets'),
                    (user['id'],  250.00, 'Health',        '2026-06-26', 'Pharmacy'),
                ]
            )
            db.commit()
