/add-expenses
---
description: Add one or more random expense rows to the local SQLite database for a given user. Use this skill whenever the user runs /add-expenses, or asks to "add fake/random/test expenses," "seed some expenses," "give user X some spending data," or "populate the expenses table." Accepts an optional user identifier (id or email) and an optional count; defaults to the most recently created user and 5 expenses.
---

---
name: add-expenses
description: /add-expenses user_id=4 count=7 months=12
---

# Add Expenses

Inserts random expense rows into the `expenses` table for an existing user —
no bundled script, just a fresh inline Python snippet each time this is triggered.

```sql
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

1. **Locate the database file.** Glob for `*.db` in the project, or read the
   app config for the path. Confirm it exists before opening it.

2. **Read the parameters** the user passed (positional or named). The three
   accepted parameters are:

   | Parameter | What it controls | Default |
   |-----------|-----------------|---------|
   | **User ID** | Which user in the `users` table the expenses are associated with. Accepts a numeric id or an email address. | most-recently created user |
   | **Count** | Total number of dummy expense entries to create. | 5 |
   | **Months** | Time span to distribute the expenses over. Inputting `6` spreads dates randomly across the last 6 months (≈ 180 days). | 6 |

3. **Resolve the target user.**
   - If the user supplied a User ID or email, look it up:
     `SELECT id, name FROM users WHERE id = ? OR email = ?`
   - If nothing was supplied, default to the most-recently created user:
     `SELECT id, name FROM users ORDER BY id DESC LIMIT 1`
   - If no user exists at all, surface that error and stop — do not create one
     here (use /seed-user for that).

4. **Determine the count and months.** Use whatever values the user passed;
   fall back to defaults (Count = 5, Months = 6) if unspecified.

5. **Insert the expenses** with an inline Python snippet shaped like this:

   ```python
   import sqlite3, random, datetime

   DB_PATH  = "<DB_PATH>"   # replace with real path
   USER_ID  = <id>          # replace with resolved user id
   COUNT    = 5             # replace with requested count
   MONTHS   = 6             # replace with requested months

   span_days = MONTHS * 30
   categories = ["Food", "Transport", "Utilities", "Entertainment",
                 "Rent", "Health", "Shopping", "Other"]

   conn = sqlite3.connect(DB_PATH)
   conn.execute("PRAGMA foreign_keys = ON")

   inserted = []
   for _ in range(COUNT):
       amount   = round(random.uniform(50, 5000), 2)   # INR range
       category = random.choice(categories)
       date     = (datetime.date.today() - datetime.timedelta(days=random.randint(0, span_days))).isoformat()
       desc     = f"{category} expense (seeded)"
       cur = conn.execute(
           "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
           (USER_ID, amount, category, date, desc),
       )
       inserted.append((cur.lastrowid, amount, category, date))

   conn.commit()
   conn.close()

   for row in inserted:
       print(f"  id={row[0]}  ₹{row[1]:.2f}  {row[2]}  {row[3]}")
   ```

6. **Report back** how many expenses were added, for which user (name + id),
   and print the table of inserted rows (id, amount, category, date).

## Notes

- Amounts are in INR (₹); use a range that feels realistic (₹50–₹5000).
- Spread dates randomly over `MONTHS * 30` days so dashboard charts look
  interesting rather than all landing on today.
- This skill only ever performs INSERTs — never delete or modify existing
  expenses.
- If the user asks for expenses in a specific category only, filter
  `random.choice` to that category list.

## Example usage

```
# Defaults — 5 expenses for the most recent user, spread over 6 months
/add-expenses

# 10 expenses for the most recent user, spread over 3 months
/add-expenses count=10 months=3

# 7 expenses for user with id 4, spread over 12 months
/add-expenses user_id=4 count=7 months=12

# Using an email address instead of an id
/add-expenses user_id=avery.brown.c2si@example.com count=5 months=6
```

## Sample run

Running `/add-expenses count=3 months=2` for a user named Shaurya (id=1) produces output like:

```
Added 3 expenses for Shaurya (id=1):
  id=12  ₹342.50  Food        2026-05-21
  id=13  ₹1874.00 Transport   2026-06-03
  id=14  ₹90.75   Health      2026-07-01
```
