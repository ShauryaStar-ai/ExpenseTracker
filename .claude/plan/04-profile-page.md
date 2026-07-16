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

The navbar currently always shows Sign in / Get started. Update it to conditionally show the user's name and a logout link:

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

> Note: this requires login (Step 3) to also store `session['user_name']` alongside `session['user_id']`. Verify or add it.

---

### Task 3 — Create `templates/profile.html`

Four sections, all extending `base.html`. No hex values anywhere — only CSS variables.

```html
{% extends "base.html" %}
{% block title %}Profile — Spendly{% endblock %}
{% block content %}

<section class="profile-section">
  <div class="profile-container">

    <!-- 1. User info card -->
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
            <th>Date</th>
            <th>Description</th>
            <th>Category</th>
            <th>Amount</th>
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

> `style="width: {{ c.pct }}%"` on the progress fill is the only allowed inline style — it carries a dynamic value that can't be a static CSS class.

---

### Task 4 — Add profile CSS to `static/css/style.css`

New classes to add (CSS variables only, no hex):

| Class | Purpose |
|---|---|
| `.profile-section` | Page-level padding/background |
| `.profile-container` | Max-width wrapper, vertical stack |
| `.profile-card` | Flex row: avatar + info side by side |
| `.avatar` | Circle, accent background, white text, initials |
| `.profile-name` | Large display font |
| `.profile-email`, `.profile-since` | Muted secondary text |
| `.stats-row` | Three-column grid |
| `.stat-card` | Bordered card, label above value |
| `.stat-label` | Small muted text |
| `.stat-value` | Large prominent number |
| `.section-block` | Vertical spacing wrapper |
| `.section-title` | Section heading |
| `.expense-table` | Full-width table, alternating rows |
| `.amount` | Right-aligned cell |
| `.badge` | Pill shape — base style |
| `.badge-food` | Food category colours (CSS vars) |
| `.badge-travel` | Travel category colours |
| `.badge-bills` | Bills category colours |
| `.badge-shopping` | Shopping category colours |
| `.badge-entertainment` | Entertainment category colours |
| `.badge-health` | Health category colours |
| `.category-list` | Unstyled list |
| `.category-row` | Flex row: name + bar + amount |
| `.category-name` | Left label, fixed min-width |
| `.category-amount` | Right label, fixed min-width |
| `.progress-bar-track` | Full-width grey track |
| `.progress-bar-fill` | Accent fill, height + border-radius |

---

## Implementation order

1. `app.py` — add `session` import + replace stub (unblocks manual testing immediately)
2. `base.html` — update navbar conditional
3. `templates/profile.html` — create the template
4. `static/css/style.css` — add profile classes
5. Run app → register → login → visit `/profile` to verify all sections render

---

## Definition of done

- [ ] `GET /profile` without session → redirects to `/login`
- [ ] `GET /profile` with session → HTTP 200
- [ ] User info card shows name, email, member-since, avatar initials
- [ ] Stats row shows total spent, transaction count, top category
- [ ] Transaction table has ≥ 3 rows with date, description, category badge, amount
- [ ] Category breakdown has ≥ 3 categories with progress bars
- [ ] Navbar shows username + Sign out when logged in
- [ ] `profile.html` contains zero hex colour values — only CSS variables
- [ ] No inline styles except the progress bar width
