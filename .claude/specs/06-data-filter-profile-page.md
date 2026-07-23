# Spec — Step 6: Data Filter for Profile Page

## 1. Overview

Add filter controls to `GET /profile` so the user can narrow the transactions table
(and the stats / category breakdown) by **category** and/or a **date range**.

The filter is submitted as a regular HTML `GET` form — no JavaScript required.
Query-string values are read in `app.py`, injected into the SQL `WHERE` clause,
and the template reflects the active filter so the form stays filled in.

---

## 2. Depends on

- **Step 5 (Backend DB — Profile Page)** — `/profile` must already read from the DB
  (the live version in `app.py` lines 90–160).

---

## 3. Route change

### `GET /profile` *(extend existing handler)*

| Item | Detail |
| --- | --- |
| URL | `/profile?category=Food&from=2026-01-01&to=2026-06-30` |
| Methods | `GET` |
| Auth | Redirect to `/login` if `session['user_id']` is not set (unchanged) |
| New query params | `category` (string or empty), `from` (YYYY-MM-DD or empty), `to` (YYYY-MM-DD or empty) |
| Success | Render `profile.html` with filtered data + active filter values echoed back |

---

## 4. Database

No schema changes.

---

## 5. Backend logic — parameterized filter query

Replace the fixed `db.execute(...)` for expenses with a dynamic query builder:

```python
category_filter = request.args.get("category", "").strip()
from_date       = request.args.get("from", "").strip()
to_date         = request.args.get("to", "").strip()

query  = "SELECT amount, category, date, description FROM expenses WHERE user_id = ?"
params = [user_id]

if category_filter:
    query += " AND category = ?"
    params.append(category_filter)

if from_date:
    query += " AND date >= ?"
    params.append(from_date)

if to_date:
    query += " AND date <= ?"
    params.append(to_date)

query += " ORDER BY date DESC"
rows = db.execute(query, params).fetchall()
```

The stats and category breakdown are computed from `rows` exactly as before —
no extra queries needed; filtered rows automatically produce filtered totals.

---

## 6. Fetch distinct categories for the dropdown

Query the user's own categories to populate the `<select>` (avoids hardcoding):

```python
category_rows = db.execute(
    "SELECT DISTINCT category FROM expenses WHERE user_id = ? ORDER BY category",
    (user_id,)
).fetchall()
all_categories = [r["category"] for r in category_rows]
```

Pass to the template: `categories_list=all_categories`.

---

## 7. Full replacement for `/profile` in `app.py`

```python
@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    from datetime import datetime
    from collections import defaultdict

    user_id = session["user_id"]
    db      = get_db()

    # --- user info ---
    user_row = db.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    dt_joined = datetime.strptime(user_row["created_at"][:10], "%Y-%m-%d")
    initials  = "".join(w[0].upper() for w in user_row["name"].split()[:2])

    user = {
        "name":         user_row["name"],
        "email":        user_row["email"],
        "member_since": dt_joined.strftime("%B %Y"),
        "initials":     initials,
    }

    # --- filter params ---
    category_filter = request.args.get("category", "").strip()
    from_date       = request.args.get("from", "").strip()
    to_date         = request.args.get("to", "").strip()

    # --- dynamic query ---
    query  = "SELECT amount, category, date, description FROM expenses WHERE user_id = ?"
    params = [user_id]

    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)
    if from_date:
        query += " AND date >= ?"
        params.append(from_date)
    if to_date:
        query += " AND date <= ?"
        params.append(to_date)

    query += " ORDER BY date DESC"
    rows = db.execute(query, params).fetchall()

    # --- transactions ---
    transactions = []
    for r in rows:
        dt = datetime.strptime(r["date"], "%Y-%m-%d")
        transactions.append({
            "date":        dt.strftime("%d %b %Y"),
            "description": r["description"] or "",
            "category":    r["category"],
            "amount":      f"₹{r['amount']:,.0f}",
        })

    # --- stats (from filtered rows) ---
    total      = sum(r["amount"] for r in rows)
    cat_totals = defaultdict(float)
    for r in rows:
        cat_totals[r["category"]] += r["amount"]

    top_category = max(cat_totals, key=cat_totals.get) if cat_totals else "—"

    stats = {
        "total_spent":       f"₹{total:,.0f}",
        "transaction_count": len(rows),
        "top_category":      top_category,
    }

    categories = [
        {
            "name":   name,
            "amount": f"₹{amount:,.0f}",
            "pct":    round((amount / total) * 100) if total else 0,
        }
        for name, amount in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
    ]

    # --- dropdown options ---
    cat_rows       = db.execute(
        "SELECT DISTINCT category FROM expenses WHERE user_id = ? ORDER BY category",
        (user_id,)
    ).fetchall()
    all_categories = [r["category"] for r in cat_rows]

    # --- active filter echo ---
    active_filter = {
        "category": category_filter,
        "from":     from_date,
        "to":       to_date,
    }

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
        all_categories=all_categories,
        active_filter=active_filter,
    )
```

---

## 8. Template changes — `profile.html`

Add a filter form **above** the transactions table (inside `.section-block`):

```html
<!-- Filter form -->
<div class="section-block">
  <h2 class="section-title">Filter Transactions</h2>
  <form class="filter-form" method="get" action="{{ url_for('profile') }}">

    <div class="filter-field">
      <label for="category">Category</label>
      <select name="category" id="category">
        <option value="">All categories</option>
        {% for cat in all_categories %}
        <option value="{{ cat }}" {% if active_filter.category == cat %}selected{% endif %}>
          {{ cat }}
        </option>
        {% endfor %}
      </select>
    </div>

    <div class="filter-field">
      <label for="from">From</label>
      <input type="date" name="from" id="from"
             value="{{ active_filter.from }}">
    </div>

    <div class="filter-field">
      <label for="to">To</label>
      <input type="date" name="to" id="to"
             value="{{ active_filter.to }}">
    </div>

    <div class="filter-actions">
      <button type="submit" class="btn btn-primary">Apply</button>
      <a href="{{ url_for('profile') }}" class="btn btn-ghost">Clear</a>
    </div>

  </form>
</div>
```

Also add a **filtered indicator** above the transactions table heading when a filter is active:

```html
{% if active_filter.category or active_filter.from or active_filter.to %}
<p class="filter-active-notice">
  Showing {{ transactions | length }} result(s)
  {% if active_filter.category %}in <strong>{{ active_filter.category }}</strong>{% endif %}
  {% if active_filter.from %}from <strong>{{ active_filter.from }}</strong>{% endif %}
  {% if active_filter.to %}to <strong>{{ active_filter.to }}</strong>{% endif %}.
  <a href="{{ url_for('profile') }}">Clear filter</a>
</p>
{% endif %}
```

---

## 9. CSS additions — `static/css/style.css`

Add at the end of the file using existing design tokens:

```css
/* ── Filter form ─────────────────────────────── */
.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.filter-field label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.filter-field select,
.filter-field input[type="date"] {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--paper-card);
  color: var(--text);
  font-size: 0.95rem;
  min-width: 10rem;
}

.filter-actions {
  display: flex;
  gap: 0.5rem;
}

.filter-active-notice {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

.filter-active-notice a {
  color: var(--accent);
  text-decoration: underline;
  margin-left: 0.5rem;
}
```

---

## 10. Files to Change

| File | Action |
| --- | --- |
| `expense-tracker/app.py` | Replace `profile()` with the filtered version above |
| `expense-tracker/templates/profile.html` | Add filter form + active-filter notice |
| `expense-tracker/static/css/style.css` | Append filter CSS at end of file |

## 11. Files to Create

None.

---

## 12. Edge Cases

| Scenario | Expected behaviour |
| --- | --- |
| No filter params | Shows all expenses (same as Step 5 behaviour) |
| Category filter only | SQL adds `AND category = ?`; stats reflect that category only |
| Date range only | SQL adds `AND date >= ?` / `AND date <= ?` |
| Both filters active | Both clauses combined with `AND` |
| `from` > `to` | Returns 0 rows — empty table, stats show ₹0 / 0 / — |
| User has no expenses matching filter | Empty transactions list; stats show zeros; no crash |
| Invalid date string in query param | SQLite date comparison simply finds no matches; no error |
| `all_categories` is empty (new user, no expenses) | Dropdown shows only "All categories"; no crash |

---

## 13. Definition of Done

- [ ] Filter form renders on `/profile` with category dropdown + from/to date inputs
- [ ] Submitting with no values shows all expenses (unchanged behaviour)
- [ ] Selecting a category filters the table to that category only
- [ ] Setting a date range filters to that range only
- [ ] Combining category + date range applies both filters
- [ ] Stats (total spent, count, top category) update to reflect filtered rows
- [ ] Category breakdown reflects filtered rows
- [ ] Active filter values are pre-filled in the form after submit
- [ ] "Clear" link resets to unfiltered view
- [ ] Filtered result count notice shows when a filter is active
- [ ] All SQL uses `?` placeholders — no f-strings in SQL
- [ ] Empty result renders without a crash

---

## 14. Implementation Order

1. Update `profile()` in `app.py` with the filter query builder.
2. Add the filter form block to `profile.html` above the transactions table.
3. Add the active-filter notice paragraph.
4. Append filter CSS to `style.css`.
5. Start the app: `python app.py`
6. Log in → visit `/profile` → confirm the unfiltered view is unchanged.
7. Select a category → verify table and stats change.
8. Set a date range → verify it narrows rows correctly.
9. Combine both filters → verify combined result.
10. Click "Clear" → confirm full list returns.
