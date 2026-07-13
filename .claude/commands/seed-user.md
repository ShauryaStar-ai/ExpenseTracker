/seed-user
---
description: Seed the local SQLite database with one randomly generated user (name, unique email, hashed password) every time the /seed-user command is invoked. Use this skill whenever the user runs /seed-user, or asks to "seed a user," "add a fake/random/test user," "create a dummy account," or "populate the users table," for the expense-tracker app with the `users` and `expenses` tables. Optionally attach a handful of random expenses to the new user if asked for test/sample data, a "user with some expenses," or a "fully populated" account.
---

---
name: seed-user
description: Seed the local SQLite database with one randomly generated user (name, unique email, hashed password) every time the /seed-user command is invoked. Use this skill whenever the user runs /seed-user, or asks to "seed a user," "add a fake/random/test user," "create a dummy account," or "populate the users table," for the expense-tracker app with the `users` and `expenses` tables. Optionally attach a handful of random expenses to the new user if asked for test/sample data, a "user with some expenses," or a "fully populated" account.
---

# Seed User

Generates one random user and inserts it directly into the `users` table of
the local SQLite database (schema below) — no bundled script, just run a
one-off Python snippet each time this is triggered.

```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount      REAL NOT NULL,
    category    TEXT NOT NULL,
    date        TEXT NOT NULL,
    description TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

## Steps to follow

1. **Locate the database file.** Search the project for a `*.db` file, or
   check the app's config / connection string for the path. Don't assume a
   filename — confirm it exists before writing to it.

2. **Confirm the `users` table exists** in that file (a quick
   `sqlite3.connect(...).execute("SELECT 1 FROM users LIMIT 1")` is enough).
   If it errors, surface that error to the user rather than guessing at the
   schema.

3. **Generate and insert one random user**, using a short inline Python
   snippet (run via the bash/code tool) shaped like this:

   ```python
   import sqlite3, hashlib, random, string

   first = random.choice(["Alex","Jordan","Taylor","Morgan","Casey","Riley","Jamie","Avery"])
   last  = random.choice(["Smith","Johnson","Lee","Brown","Garcia","Davis","Miller","Wilson"])
   name  = f"{first} {last}"
   suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
   email = f"{first.lower()}.{last.lower()}.{suffix}@example.com"
   plaintext_password = "".join(random.choices(string.ascii_letters + string.digits, k=12))
   password_hash = hashlib.sha256(plaintext_password.encode()).hexdigest()

   conn = sqlite3.connect("<DB_PATH>")
   conn.execute("PRAGMA foreign_keys = ON")
   cur = conn.execute(
       "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
       (name, email, password_hash),
   )
   user_id = cur.lastrowid
   conn.commit()
   conn.close()

   print(f"id={user_id} name={name} email={email} password={plaintext_password}")
   ```

   Replace `<DB_PATH>` with the real path found in step 1. Vary the random
   pools/logic a bit each time if you like — the point of this approach is
   that Claude writes it fresh per call rather than reusing a fixed script.

4. **If sample expenses were requested** (e.g. "seed a user with some
   expenses"), extend the same snippet with a loop before `conn.commit()`:

   ```python
   import datetime
   categories = ["Food","Transport","Utilities","Entertainment","Rent","Health","Shopping","Other"]
   for _ in range(N):  # N = however many the user asked for, default 3-5
       amount = round(random.uniform(3, 500), 2)
       category = random.choice(categories)
       date = (datetime.date.today() - datetime.timedelta(days=random.randint(0, 90))).isoformat()
       conn.execute(
           "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
           (user_id, amount, category, date, f"{category} expense (seeded)"),
       )
   ```

5. **Report back** the generated `id`, `name`, `email`, and plaintext
   password — this is the only time the plaintext is visible, since only the
   hash is stored in the DB. If expenses were added, mention how many.

## Notes

- Password hashing uses `sha256` here as a placeholder. If the app's real
  auth flow uses bcrypt/argon2/scrypt/PBKDF2, hash with that instead so the
  seeded user can actually log in through the real app, not just exist as a
  DB row.
- Handle a `sqlite3.IntegrityError` (duplicate email) by regenerating the
  email and retrying once — collisions should be rare given the random
  suffix, but don't let the whole command fail silently on one.
- This skill only ever performs INSERTs — never delete or modify existing
  users when seeding.