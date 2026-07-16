# Implementation Plan: Step 4 — Profile Page

## Goal
Replace the `/profile` stub with a fully-designed page showing hardcoded data.
No DB queries in this step — all data is hardcoded in `app.py` and passed to the template.

---

## Prerequisites (must be true before starting)
- Step 3 (login/logout) is done: `session['user_id']` is set on login and cleared on logout.
- `flask.session` is imported in `app.py`.
- `base.html` navbar shows username + logout link when `session['user_id']` is set.

---

## Files to change

| File | Action |
|---|---|
| `expense-tracker/app.py` | Replace `/profile` stub with real view |
| `expense-tracker/templates/base.html` | Update navbar for logged-in state |
| `expense-tracker/templates/profile.html` | **Create** — full profile page |
| `expense-tracker/static/css/style.css` | Add profile-page CSS classes |

---

## Step-by-step tasks

### Task 1 — Update `app.py` imports and `/profile` route

1. Add `session` to the Flask import line (line 2):
   ```python
   from flask import Flask, render_template, request, redirect, url_for, session
   ```

2. Replace the stub at lines 72–74:
   ```python
   @app.route("/profile")
   def profile():
       if not session.get("user_id"):
           return redirect(url_for("login"))

       user = {
           "name": "Nitish Kumar",
           "email": "nitish@example.com",
           "member_since": "January 2025",
           "initials": "NK",
       }

       stats = {
           "total_spent": "₹7,019",
           "transaction_count": 8,
           "top_category": "Travel",
       }

       transactions = [
           {"date": "01 Jul 2026", "description": "Electricity bill",  "category": "Bills",         "amount": "₹800"},
           {"date": "30 Jun 2026", "description": "Restaurant lunch",  "category": "Food",          "amount": "₹320"},
           {"date": "29 Jun 2026", "description": "Movie tickets",     "category": "Entertainment", "amount": "₹500"},
           {"date": "28 Jun 2026", "description": "Groceries",         "category": "Food",          "amount": "₹450"},
           {"date": "27 Jun 2026", "description": "New shirt",         "category": "Shopping",      "amount": "₹999"},
           {"date": "26 Jun 2026", "description": "Pharmacy",          "category": "Health",        "amount": "₹250"},
           {"date": "25 Jun 2026", "description": "Auto to office",    "category": "Travel",        "amount": "₹1,200"},
           {"date": "22 Jun 2026", "description": "Weekend trip",      "category": "Travel",        "amount": "₹2,500"},
       ]

       categories = [
           {"name": "Travel",        "amount": "₹3,700", "pct": 53},
           {"name": "Shopping",      "amount": "₹999",   "pct": 14},
           {"name": "Bills",         "amount": "₹800",   "pct": 11},
           {"name": "Food",          "amount": "₹770",   "pct": 11},
           {"name": "Entertainment", "amount": "₹500",   "pct": 7},
           {"name": "Health",        "amount": "₹250",   "pct": 4},
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

### Task 2 — Update `base.html` navbar for logged-in state

The navbar currently always shows Sign in / Get started links. Update it to show the user's name and a logout link when a session exists:

```html
<div class="nav-links">
    {% if session.get("user_id") %}
        <span class="nav-username">{{ session.get("user_name", "Account") }}</span>
        <a href="{{ url_for('logout') }}" class="nav-cta">Sign out</a>
    {% else %}
        <a href="{{ url_for('login') }}">Sign in</a>
        <a href="{{ url_for('register') }}" class="nav-cta">Get started</a>
    {% endif %}
</div>
```

> Note: This requires that login also stores `session['user_name']` alongside `session['user_id']`. Verify Step 3 does this, or add it.

---

### Task 3 — Create `templates/profile.html`

Four sections, all extending `base.html`:

```
{% extends "base.html" %}
{% block title %}Profile — Spendly{% endblock %}
{% block content %}

  <!-- 1. User info card -->
  <section class="profile-section">
    <div class="profile-container">
      <div class="profile-card">
        <div class="avatar">{{ user.initials }}</div>
        <div class="profile-info">
          <h1 class="profile-name">{{ user.name }}</h1>
          <p class="profile-email">{{ user.email }}</p>
          <p class="profile-since">Member since {{ user.member_since }}</p>
        </div>
      </div>

      <!-- 2. Summary stats row -->
      <div class="stats-row">
        <div class="stat-card">
          <span class="stat-label">Total Spent</span>
          <span class="stat-value">{{ stats.total_spent }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Transactions</span>
          <span class="stat-value">{{ stats.transaction_count }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Top Category</span>
          <span class="stat-value">{{ stats.top_category }}</span>
        </div>
      </div>

      <!-- 3. Transaction history table -->
      <div class="section-block">
        <h2 class="section-title">Recent Transactions</h2>
        <table class="expense-table">
          <thead>
            <tr>
              <th>Date</th><th>Description</th><th>Category</th><th>Amount</th>
            </tr>
          </thead>
          <tbody>
            {% for t in transactions %}
            <tr>
              <td>{{ t.date }}</td>
              <td>{{ t.description }}</td>
              <td><span class="badge badge-{{ t.category | lower }}">{{ t.category }}</span></td>
              <td class="amount">{{ t.amount }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>

      <!-- 4. Category breakdown -->
      <div class="section-block">
        <h2 class="section-title">Spending by Category</h2>
        <ul class="category-list">
          {% for c in categories %}
          <li class="category-row">
            <span class="category-name">{{ c.name }}</span>
            <div class="progress-bar-track">
              <div class="progress-bar-fill" style="width: {{ c.pct }}%"></div>
            </div>
            <span class="category-amount">{{ c.amount }}</span>
          </li>
          {% endfor %}
        </ul>
      </div>

    </div>
  </section>

{% endblock %}
```

> The `style="width: {{ c.pct }}%"` on the progress bar is the only inline style allowed — it carries a dynamic value that cannot be expressed as a static CSS class.

---

### Task 4 — Add CSS for profile page to `style.css`

New classes needed (use only CSS variables, no hex values):

- `.profile-section`, `.profile-container` — page layout wrapper
- `.profile-card` — flex row: avatar + info
- `.avatar` — circle with accent background, white text, initials
- `.profile-name`, `.profile-email`, `.profile-since` — typography
- `.stats-row` — three-column grid
- `.stat-card` — bordered card with label + value
- `.stat-label`, `.stat-value` — typography
- `.section-block` — spacing wrapper for table + breakdown
- `.section-title` — heading style
- `.expense-table` — full-width table, striped or bordered rows
- `.amount` — right-aligned, monospace-ish
- `.badge` — pill shape; category-specific colour via modifier classes:
  - `.badge-food`, `.badge-travel`, `.badge-bills`, `.badge-shopping`, `.badge-entertainment`, `.badge-health`
  - Each uses an existing or new CSS variable pair (background + text) — no hex
- `.category-list`, `.category-row` — flex layout for breakdown rows
- `.category-name`, `.category-amount` — text sizing
- `.progress-bar-track` — grey background bar
- `.progress-bar-fill` — accent-coloured fill (width set inline from template)

---

## Definition of done checklist

- [ ] `GET /profile` without session → redirects to `/login`
- [ ] `GET /profile` with session → HTTP 200
- [ ] User info card shows name, email, member-since, avatar initials
- [ ] Stats row shows total spent, transaction count, top category
- [ ] Transaction table has ≥ 3 rows with date, description, category badge, amount
- [ ] Category breakdown has ≥ 3 categories with progress bars
- [ ] Navbar shows username + Sign out when logged in
- [ ] `profile.html` contains zero hex colour values — only CSS variables
- [ ] No inline styles except the progress bar width

---

## Implementation order

1. `app.py` — add `session` import + replace stub (unblocks manual testing immediately)
2. `base.html` — update navbar (needed for logged-in state to show)
3. `templates/profile.html` — create the template
4. `static/css/style.css` — add profile CSS classes
5. Run the app and walk through the flow: register → login → `/profile`
