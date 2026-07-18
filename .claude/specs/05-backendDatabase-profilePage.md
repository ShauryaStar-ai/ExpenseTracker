# Spec — Step 5: Backend Database — Profile Page

## 1. Overview

Replace the hardcoded dummy data in `GET /profile` with real SQLite queries.
The page structure and CSS already exist from Step 4 — this step is **purely a backend change to `app.py`**.
No template changes, no CSS changes.

---

## 2. Depends on

- **Step 1 (Database)** — `get_db()`, `users` table, `expenses` table must exist.
- **Step 3 (Login)** — `session['user_id']` must be set on login so the profile route knows which user to query.
- **Step 4 (Profile Page)** — `profile.html` template must exist and accept `user`, `stats`, `transactions`, `categories` variables.

---

## 3. Route

### `GET /profile` *(replace stub data with DB queries)*

| Item | Detail |
| --- | --- |
| URL | `/profile` |
| Methods | `GET` |
| Auth | Redirect to `/login` if `session['user_id']` is not set |
| Success | Render `profile.html` with live data from DB |

---

## 4. Database

No schema changes. Reads from existing `users` and `expenses` tables.

---

## 5. Queries to Write

### A. Fetch the logged-in user

```python
user_id = session["user_id"]
db = get_db()
user_row = db.execute(
    "SELECT name, email, created_at FROM users WHERE id = ?",
    (user_id,)
).fetchone()
```

Then build the `user` dict:

```python
from datetime import datetime

dt = datetime.strptime(user_row["created_at"][:10], "%Y-%m-%d")
member_since = dt.strftime("%B %Y")          # e.g. "January 2025"
initials = "".join(w[0].upper() for w in user_row["name"].split()[:2])

user = {
    "name":         user_row["name"],
    "email":        user_row["email"],
    "member_since": member_since,
    "initials":     initials,
}
```

### B. Fetch all expenses for the user

```python
rows = db.execute(
    """
    SELECT amount, category, date, description
    FROM   expenses
    WHERE  user_id = ?
    ORDER  BY date DESC
    """,
    (user_id,)
).fetchall()
```

### C. Build the `transactions` list

Format `date` from `YYYY-MM-DD` (stored in DB) to `DD Mon YYYY` (shown in table):

```python
transactions = []
for r in rows:
    dt = datetime.strptime(r["date"], "%Y-%m-%d")
    transactions.append({
        "date":        dt.strftime("%d %b %Y"),   # e.g. "01 Jul 2026"
        "description": r["description"] or "",
        "category":    r["category"],
        "amount":      f"₹{r['amount']:,.0f}",    # e.g. "₹1,200"
    })
```

### D. Compute `stats`

```python
total = sum(r["amount"] for r in rows)
count = len(rows)

# Top category by total spend
from collections import defaultdict
cat_totals = defaultdict(float)
for r in rows:
    cat_totals[r["category"]] += r["amount"]

top_category = max(cat_totals, key=cat_totals.get) if cat_totals else "—"

stats = {
    "total_spent":       f"₹{total:,.0f}",
    "transaction_count": count,
    "top_category":      top_category,
}
```

### E. Compute `categories` breakdown

```python
categories = []
for name, amount in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True):
    pct = round((amount / total) * 100) if total else 0
    categories.append({
        "name":   name,
        "amount": f"₹{amount:,.0f}",
        "pct":    pct,
    })
```

---

## 6. Full Replacement for `/profile` in `app.py`

Replace the entire existing `profile()` function (lines 90–134) with:

```python
@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    from datetime import datetime
    from collections import defaultdict

    user_id = session["user_id"]
    db = get_db()

    # --- user info ---
    user_row = db.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    dt_joined = datetime.strptime(user_row["created_at"][:10], "%Y-%m-%d")
    initials = "".join(w[0].upper() for w in user_row["name"].split()[:2])

    user = {
        "name":         user_row["name"],
        "email":        user_row["email"],
        "member_since": dt_joined.strftime("%B %Y"),
        "initials":     initials,
    }

    # --- expenses ---
    rows = db.execute(
        "SELECT amount, category, date, description FROM expenses "
        "WHERE user_id = ? ORDER BY date DESC",
        (user_id,)
    ).fetchall()

    transactions = []
    for r in rows:
        dt = datetime.strptime(r["date"], "%Y-%m-%d")
        transactions.append({
            "date":        dt.strftime("%d %b %Y"),
            "description": r["description"] or "",
            "category":    r["category"],
            "amount":      f"₹{r['amount']:,.0f}",
        })

    # --- stats ---
    total = sum(r["amount"] for r in rows)
    cat_totals = defaultdict(float)
    for r in rows:
        cat_totals[r["category"]] += r["amount"]

    top_category = max(cat_totals, key=cat_totals.get) if cat_totals else "—"

    stats = {
        "total_spent":       f"₹{total:,.0f}",
        "transaction_count": len(rows),
        "top_category":      top_category,
    }

    # --- category breakdown ---
    categories = [
        {
            "name":   name,
            "amount": f"₹{amount:,.0f}",
            "pct":    round((amount / total) * 100) if total else 0,
        }
        for name, amount in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
    )
```

---

## 7. Files to Change

| File | Action |
| --- | --- |
| `expense-tracker/app.py` | Replace `profile()` function with the DB-backed version above |

---

## 8. Files to Create

None.

---

## 9. New Imports

Both `datetime` and `defaultdict` are stdlib — no new pip packages.
Import them **inside the function** (as shown above) to keep the module-level imports clean.

---

## 10. Edge Cases

| Scenario | Expected behaviour |
| --- | --- |
| User has no expenses | `transactions = []`, `stats = {"total_spent": "₹0", "transaction_count": 0, "top_category": "—"}`, `categories = []` |
| `description` is NULL in DB | Replaced with `""` so template renders an empty cell, not `None` |
| Amount formatting | `₹1,200` not `₹1200` — use `:,.0f` format spec |
| `created_at` truncation | `[:10]` strips the time portion from `datetime('now')` output |

---

## 11. Definition of Done

- [ ] `GET /profile` without a session → redirects to `/login`
- [ ] `GET /profile` with a session → HTTP 200, no hardcoded names visible
- [ ] User card shows the **actual logged-in user's** name, email, member-since
- [ ] Avatar initials derived from the real user's name
- [ ] Transactions table shows rows from the `expenses` DB table, not the hardcoded list
- [ ] Dates display as `DD Mon YYYY` (e.g. `01 Jul 2026`)
- [ ] Amounts display as `₹1,200` (comma-separated, no decimals)
- [ ] Stats reflect actual DB totals (total spent, count, top category)
- [ ] Category breakdown percentages sum to ~100%
- [ ] A user with zero expenses sees no crash — empty table and `—` for top category
- [ ] All SQL uses parameterized queries — no f-strings in SQL

---

## 12. Implementation Order

1. Replace `profile()` in `app.py` with the DB-backed version.
2. Start the app: `python app.py`
3. Register a new user (or use `demo@spendly.in` / `password123`).
4. Log in and visit `/profile` — verify the real name, email, and seeded expenses appear.
5. Create a second user with no expenses — confirm the empty-state renders without error.
