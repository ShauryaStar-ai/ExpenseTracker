# Spec — Step 7: Add Expense GUI

## 1. Overview

Give the logged-in user a friendly form to add a new expense directly from their
profile page.  An **"+ Add Expense"** button sits at the top of `/profile`; clicking
it opens a modal dialog containing the form.  Submitting the form `POST`s to
`/expenses/add`, which writes the new row to the `expenses` table and redirects
back to `/profile` so the updated totals and transaction list are visible
immediately.

No new page or template file is needed — the modal lives inside `profile.html`
and is toggled with a few lines of vanilla JavaScript.

---

## 2. Depends on

- **Step 5 (Backend DB — Profile Page)** — `/profile` reads from the DB (done).
- **Step 6 (Data Filter)** — filter query already works; adding an expense must
  not break it (done).

---

## 3. Route changes

### `POST /expenses/add`  *(replace existing stub)*

| Item | Detail |
| --- | --- |
| URL | `/expenses/add` |
| Methods | `GET` (redirect guard), `POST` (form handler) |
| Auth | Redirect to `/login` if `session['user_id']` is not set |
| Form fields | `amount` (required), `category` (required), `date` (required), `description` (optional) |
| Success | Insert row → `redirect(url_for('profile'))` |
| Validation error | Re-render `profile.html` with `add_error="…"` and `show_modal=True` so the modal re-opens with the message |

The current stub at `app.py` line 190–192 is replaced with the full handler shown
in §5 below.

---

## 4. Database

No schema changes — the `expenses` table already has all required columns:

```
id, user_id, amount, category, date, description, created_at
```

Allowed categories (match the seed data and dropdown):
`Food`, `Travel`, `Bills`, `Shopping`, `Entertainment`, `Health`, `Other`

---

## 5. Backend logic — `POST /expenses/add`

```python
@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if request.method == "GET":
        return redirect(url_for("profile"))

    amount_str  = request.form.get("amount", "").strip()
    category    = request.form.get("category", "").strip()
    date_str    = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()

    # --- validation ---
    if not amount_str or not category or not date_str:
        return _profile_with_error("Amount, category, and date are required.")

    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return _profile_with_error("Amount must be a positive number.")

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return _profile_with_error("Date must be in YYYY-MM-DD format.")

    user_id = session["user_id"]
    db = get_db()
    db.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, date_str, description or None)
    )
    db.commit()
    return redirect(url_for("profile"))
```

Add a small private helper above `add_expense` to avoid duplicating the full
profile render logic:

```python
def _profile_with_error(message):
    """Re-render the profile page with the add-expense modal open and an error."""
    # Re-use the profile() view data — import url_for and call render_template directly.
    # Simplest approach: set a flash or pass error through session, then redirect.
    # We use a query-string flag so no session writes are needed.
    from urllib.parse import urlencode
    return redirect(url_for("profile") + "?" + urlencode({"add_error": message}))
```

Then in `profile()`, read the error back and pass it to the template:

```python
add_error  = request.args.get("add_error", "")
show_modal = bool(add_error)   # re-open the modal automatically
```

Pass both to `render_template("profile.html", ..., add_error=add_error, show_modal=show_modal)`.

---

## 6. Template changes — `profile.html`

### 6a. "Add Expense" button

Place the button at the top of the profile content area, beside or below the
user stats section heading:

```html
<div class="section-header-row">
  <h2 class="section-title">My Expenses</h2>
  <button class="btn btn-primary" id="open-add-modal">+ Add Expense</button>
</div>
```

### 6b. Modal HTML

Add at the **bottom** of `{% block content %}`, before `{% endblock %}`:

```html
<!-- Add Expense Modal -->
<div class="modal-overlay" id="add-expense-modal" role="dialog"
     aria-modal="true" aria-labelledby="modal-title">
  <div class="modal-card">
    <div class="modal-header">
      <h2 class="modal-title" id="modal-title">Add Expense</h2>
      <button class="modal-close" id="close-modal" aria-label="Close">&times;</button>
    </div>

    {% if add_error %}
    <p class="auth-error">{{ add_error }}</p>
    {% endif %}

    <form method="post" action="{{ url_for('add_expense') }}" class="add-expense-form">
      <div class="form-field">
        <label for="amount">Amount (₹)</label>
        <input type="number" id="amount" name="amount" min="1" step="0.01"
               placeholder="e.g. 450" required>
      </div>

      <div class="form-field">
        <label for="category">Category</label>
        <select id="category" name="category" required>
          <option value="" disabled selected>Select a category</option>
          <option value="Food">Food</option>
          <option value="Travel">Travel</option>
          <option value="Bills">Bills</option>
          <option value="Shopping">Shopping</option>
          <option value="Entertainment">Entertainment</option>
          <option value="Health">Health</option>
          <option value="Other">Other</option>
        </select>
      </div>

      <div class="form-field">
        <label for="date">Date</label>
        <input type="date" id="date" name="date" required>
      </div>

      <div class="form-field">
        <label for="description">Description <span class="optional">(optional)</span></label>
        <input type="text" id="description" name="description"
               placeholder="e.g. Grocery run" maxlength="200">
      </div>

      <div class="form-actions">
        <button type="submit" class="btn btn-primary">Save Expense</button>
        <button type="button" class="btn btn-ghost" id="cancel-modal">Cancel</button>
      </div>
    </form>
  </div>
</div>
```

### 6c. JavaScript to open / close the modal

Add inside `{% block scripts %}`:

```html
{% block scripts %}
<script>
  const overlay   = document.getElementById('add-expense-modal');
  const openBtn   = document.getElementById('open-add-modal');
  const closeBtn  = document.getElementById('close-modal');
  const cancelBtn = document.getElementById('cancel-modal');

  function openModal()  { overlay.classList.add('modal-visible'); }
  function closeModal() { overlay.classList.remove('modal-visible'); }

  openBtn.addEventListener('click', openModal);
  closeBtn.addEventListener('click', closeModal);
  cancelBtn.addEventListener('click', closeModal);

  // Close when clicking the dark overlay background
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
  });

  // Re-open automatically if there was a validation error
  {% if show_modal %}openModal();{% endif %}
</script>
{% endblock %}
```

---

## 7. CSS additions — `static/css/style.css`

Append at the end of the file using existing design tokens:

```css
/* ── Add Expense button row ───────────────────── */
.section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

/* ── Modal overlay ────────────────────────────── */
.modal-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 200;
  align-items: center;
  justify-content: center;
}

.modal-overlay.modal-visible {
  display: flex;
}

.modal-card {
  background: var(--paper-card);
  border-radius: var(--radius);
  padding: 2rem;
  width: min(480px, 92vw);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text);
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-muted);
  line-height: 1;
}

.modal-close:hover { color: var(--text); }

/* ── Add-expense form fields ──────────────────── */
.add-expense-form .form-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 1rem;
}

.add-expense-form .form-field label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.add-expense-form .form-field .optional {
  font-weight: 400;
  text-transform: none;
  letter-spacing: 0;
}

.add-expense-form input,
.add-expense-form select {
  padding: 0.55rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--paper);
  color: var(--text);
  font-size: 0.95rem;
}

.add-expense-form input:focus,
.add-expense-form select:focus {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
}
```

---

## 8. Files to Change

| File | Action |
| --- | --- |
| `expense-tracker/app.py` | Replace `add_expense` stub; add `_profile_with_error`; extend `profile()` to read `add_error` and `show_modal` |
| `expense-tracker/templates/profile.html` | Add button row, modal HTML, and JS block |
| `expense-tracker/static/css/style.css` | Append modal + form CSS at end of file |

## 9. Files to Create

None.

---

## 10. Edge Cases

| Scenario | Expected behaviour |
| --- | --- |
| Missing required field | Redirect to `/profile?add_error=…`; modal re-opens with message |
| Amount is 0 or negative | Validation rejects it; modal re-opens with error |
| Amount is non-numeric (e.g. "abc") | `float()` raises `ValueError`; error shown |
| Invalid date format | `datetime.strptime` raises `ValueError`; error shown |
| Description left blank | Stored as `NULL` in DB; profile shows empty string |
| User not logged in | Redirect to `/login` |
| `GET /expenses/add` (direct URL visit) | Redirect to `/profile` silently |
| Concurrent submissions | SQLite row-level locking handles it; no special code needed |

---

## 11. Definition of Done

- [ ] `+ Add Expense` button is visible on `/profile` for logged-in users
- [ ] Clicking the button opens the modal without a page reload
- [ ] Form contains: Amount (₹), Category (dropdown), Date, Description (optional)
- [ ] Submitting a valid form saves the expense to the DB and redirects to `/profile`
- [ ] New expense appears at the top of the transactions table immediately
- [ ] Stats (total spent, count, top category) update to include the new expense
- [ ] Submitting with a missing required field shows an error inside the modal
- [ ] Submitting a non-positive amount shows an error inside the modal
- [ ] Clicking "Cancel", "×", or outside the modal closes it without submitting
- [ ] All SQL uses `?` placeholders — no f-strings in SQL
- [ ] Existing filter functionality (Step 6) still works after adding an expense

---

## 12. Implementation Order

1. Add `_profile_with_error()` helper and `add_error`/`show_modal` reads to `profile()` in `app.py`.
2. Replace the `add_expense` stub with the full `POST` handler.
3. Add `.section-header-row` button and the modal HTML block to `profile.html`.
4. Add the `{% block scripts %}` JS to `profile.html`.
5. Append modal and form CSS to `style.css`.
6. Start the app: `python app.py`
7. Log in → click `+ Add Expense` → confirm modal opens.
8. Submit with all fields filled → confirm expense appears in the list.
9. Submit with amount blank → confirm error + modal re-opens.
10. Submit with amount `0` → confirm validation error.
11. Confirm existing category filter (Step 6) still works.
