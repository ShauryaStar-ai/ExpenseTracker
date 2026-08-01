# Spec — Step 8: Edit Expense on Profile Page

## 1. Overview

Add an **Edit** button to each row in the transactions table on `/profile`.
Clicking it opens a modal pre-filled with that expense's current values.
Submitting the modal POSTs to `POST /expenses/<id>/edit`, which validates the
input, updates the database record, and redirects back to `/profile`.

The pattern mirrors Step 7 (Add Expense modal) so the approach is already
familiar: data attributes on the button populate the modal via JavaScript,
and the form action is set dynamically to include the expense ID.

---

## 2. Depends on

- **Step 7 (Add Expense GUI)** — the Add Expense modal, `.modal-card` CSS,
  and `add_expense` route must already exist.
- **Step 6 (Filter)** — `/profile` passes `transactions` list; this step adds
  `id` to each transaction dict so the template can build edit links.

---

## 3. Route change

### `POST /expenses/<int:id>/edit` *(replace stub)*

| Item | Detail |
| --- | --- |
| URL | `/expenses/<id>/edit` |
| Methods | `GET`, `POST` |
| Auth | Redirect to `/login` if `session['user_id']` is not set |
| Ownership check | Fetch the expense; if it doesn't exist or `user_id` doesn't match session → `abort(403)` |
| `GET` | Redirect to `/profile` (no standalone edit page) |
| `POST` success | Update DB, redirect to `url_for('profile')` |
| `POST` error | Redirect to `/profile` with `edit_error=<message>&edit_id=<id>` query params so the modal re-opens |

---

## 4. Database

No schema changes. The `expenses` table already has `id`, `amount`, `category`,
`date`, `description`.

---

## 5. Backend — `app.py`

### 5a. Add `id` to the `transactions` list in `profile()`

In the `profile()` route (around line 134), the query currently selects
`amount, category, date, description`. Add `id` to the `SELECT`:

```python
query = "SELECT id, amount, category, date, description FROM expenses WHERE user_id = ?"
```

Then include `id` in each transaction dict:

```python
transactions.append({
    "id":          r["id"],
    "date":        dt.strftime("%d %b %Y"),
    "date_raw":    r["date"],          # YYYY-MM-DD — needed to pre-fill date input
    "description": r["description"] or "",
    "category":    r["category"],
    "amount":      f"₹{r['amount']:,.0f}",
    "amount_raw":  r["amount"],        # numeric — needed to pre-fill amount input
})
```

Also capture edit error / edit id from query params (same pattern as `add_error`):

```python
edit_error   = request.args.get("edit_error", "")
edit_id      = request.args.get("edit_id", "")
show_edit_modal = bool(edit_error and edit_id)
```

Pass them to the template:

```python
return render_template(
    "profile.html",
    ...
    edit_error=edit_error,
    edit_id=edit_id,
    show_edit_modal=show_edit_modal,
)
```

### 5b. Helper for edit errors

Add alongside `_profile_with_error`:

```python
def _profile_with_edit_error(message, expense_id):
    from urllib.parse import urlencode
    return redirect(url_for("profile") + "?" + urlencode({
        "edit_error": message,
        "edit_id":    expense_id,
    }))
```

### 5c. Full replacement for `edit_expense()`

Replace the stub at line 237 with:

```python
@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if request.method == "GET":
        return redirect(url_for("profile"))

    db  = get_db()
    row = db.execute(
        "SELECT id, user_id FROM expenses WHERE id = ?", (id,)
    ).fetchone()

    if not row or row["user_id"] != session["user_id"]:
        abort(403)

    amount_str  = request.form.get("amount", "").strip()
    category    = request.form.get("category", "").strip()
    date_str    = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()

    if not amount_str or not category or not date_str:
        return _profile_with_edit_error("Amount, category, and date are required.", id)

    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return _profile_with_edit_error("Amount must be a positive number.", id)

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return _profile_with_edit_error("Date must be in YYYY-MM-DD format.", id)

    db.execute(
        "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ?",
        (amount, category, date_str, description or None, id)
    )
    db.commit()
    return redirect(url_for("profile"))
```

---

## 6. Template changes — `profile.html`

### 6a. Add Actions column to the transactions table

Add a fifth header cell and a matching data cell per row:

```html
<thead>
  <tr>
    <th>Date</th>
    <th>Description</th>
    <th>Category</th>
    <th>Amount</th>
    <th></th>   {# actions column — no heading #}
  </tr>
</thead>
<tbody>
  {% for t in transactions %}
  <tr>
    <td>{{ t.date }}</td>
    <td>{{ t.description }}</td>
    <td><span class="badge badge-{{ t.category | lower }}">{{ t.category }}</span></td>
    <td class="amount">{{ t.amount }}</td>
    <td class="row-actions">
      <button class="btn-row-edit"
              data-id="{{ t.id }}"
              data-amount="{{ t.amount_raw }}"
              data-category="{{ t.category }}"
              data-date="{{ t.date_raw }}"
              data-description="{{ t.description }}"
              aria-label="Edit expense">Edit</button>
    </td>
  </tr>
  {% endfor %}
</tbody>
```

### 6b. Add the Edit Expense modal

Place it directly below the Add Expense modal (before `{% endblock %}`):

```html
<!-- Edit Expense Modal -->
<div class="modal-overlay" id="edit-expense-modal" role="dialog"
     aria-modal="true" aria-labelledby="edit-modal-title">
  <div class="modal-card">
    <div class="modal-header">
      <h2 class="modal-title" id="edit-modal-title">Edit Expense</h2>
      <button class="modal-close" id="close-edit-modal" aria-label="Close">&times;</button>
    </div>

    {% if edit_error %}
    <p class="auth-error">{{ edit_error }}</p>
    {% endif %}

    <form method="post" id="edit-expense-form" class="add-expense-form">
      <div class="form-field">
        <label for="edit-amount">Amount (₹)</label>
        <input type="number" id="edit-amount" name="amount" min="1" step="0.01" required>
      </div>
      <div class="form-field">
        <label for="edit-category">Category</label>
        <select id="edit-category" name="category" required>
          <option value="" disabled>Select a category</option>
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
        <label for="edit-date">Date</label>
        <input type="date" id="edit-date" name="date" required>
      </div>
      <div class="form-field">
        <label for="edit-description">Description <span class="optional">(optional)</span></label>
        <input type="text" id="edit-description" name="description" maxlength="200">
      </div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">Save Changes</button>
        <button type="button" class="btn btn-ghost" id="cancel-edit-modal">Cancel</button>
      </div>
    </form>
  </div>
</div>
```

### 6c. JavaScript — add to the existing `{% block scripts %}`

Append inside the existing `<script>` block, after the Add modal logic:

```javascript
const editOverlay    = document.getElementById('edit-expense-modal');
const editForm       = document.getElementById('edit-expense-form');
const closeEditBtn   = document.getElementById('close-edit-modal');
const cancelEditBtn  = document.getElementById('cancel-edit-modal');

function openEditModal()  { editOverlay.classList.add('modal-visible'); }
function closeEditModal() { editOverlay.classList.remove('modal-visible'); }

closeEditBtn.addEventListener('click', closeEditModal);
cancelEditBtn.addEventListener('click', closeEditModal);
editOverlay.addEventListener('click', (e) => { if (e.target === editOverlay) closeEditModal(); });

document.querySelectorAll('.btn-row-edit').forEach(btn => {
  btn.addEventListener('click', () => {
    const id = btn.dataset.id;
    editForm.action = `/expenses/${id}/edit`;
    document.getElementById('edit-amount').value      = btn.dataset.amount;
    document.getElementById('edit-category').value    = btn.dataset.category;
    document.getElementById('edit-date').value        = btn.dataset.date;
    document.getElementById('edit-description').value = btn.dataset.description;
    openEditModal();
  });
});

{% if show_edit_modal %}
// Re-open after a validation error redirect
const errBtn = document.querySelector(`.btn-row-edit[data-id="{{ edit_id }}"]`);
if (errBtn) errBtn.click();
{% endif %}
```

---

## 7. CSS additions — `static/css/style.css`

Append at the end of the file (or at the end of the Hello Kitty `<style>` block
in `profile.html` if you want it theme-scoped):

```css
/* ── Expense table actions column ─────────────────────────────── */
.row-actions {
  text-align: right;
  white-space: nowrap;
}

.btn-row-edit {
  font-size: 0.8rem;
  padding: 0.2rem 0.6rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--paper-card);
  color: var(--accent);
  cursor: pointer;
  font-weight: 600;
}

.btn-row-edit:hover {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
```

---

## 8. Files to Change

| File | Action |
| --- | --- |
| `expense-tracker/app.py` | Add `id` + `date_raw` + `amount_raw` to `transactions`; add `edit_error`/`edit_id`/`show_edit_modal`; add `_profile_with_edit_error()`; replace `edit_expense()` stub |
| `expense-tracker/templates/profile.html` | Add Actions column to table; add Edit modal HTML; extend JS block |
| `expense-tracker/static/css/style.css` | Append `.row-actions` and `.btn-row-edit` styles |

## 9. Files to Create

None.

---

## 10. Edge Cases

| Scenario | Expected behaviour |
| --- | --- |
| User edits an expense they don't own | `abort(403)` — Flask returns a 403 page |
| Expense ID does not exist | `abort(403)` — same path (no info leak) |
| Empty amount / category / date | Redirect back to profile with error, edit modal re-opens pre-filled |
| Amount is zero or negative | Redirect back with "Amount must be a positive number." |
| Bad date format | Redirect back with "Date must be in YYYY-MM-DD format." |
| Description left blank | Stored as `NULL` in DB (same as add expense) |
| Filter is active when Edit is clicked | Edit still works; after redirect the filter resets (same as add expense) |
| No expenses on profile | No Edit buttons rendered; no JS errors |

---

## 11. Definition of Done

- [ ] Each row in the transactions table has an Edit button
- [ ] Clicking Edit opens a modal pre-filled with that row's amount, category, date, description
- [ ] Submitting the modal updates the record in the DB and redirects to `/profile`
- [ ] Updated values are immediately visible in the table after redirect
- [ ] Missing required fields show an error and re-open the edit modal
- [ ] Negative or zero amount shows an error and re-opens the modal
- [ ] A user cannot edit another user's expense (403 response)
- [ ] All SQL uses `?` placeholders — no f-strings in SQL
- [ ] GET `/expenses/<id>/edit` redirects to `/profile` (no standalone page)

---

## 12. Implementation Order

1. Update the `SELECT` query and `transactions` dict in `profile()` to include `id`, `date_raw`, `amount_raw`.
2. Add `edit_error`, `edit_id`, `show_edit_modal` to `profile()` and pass to template.
3. Add `_profile_with_edit_error()` helper in `app.py`.
4. Replace the `edit_expense()` stub with the full handler.
5. Add the Actions `<th>` and per-row Edit button to `profile.html`.
6. Add the Edit Expense modal HTML to `profile.html`.
7. Extend the JS block with edit modal logic and error re-open logic.
8. Append `.row-actions` and `.btn-row-edit` CSS.
9. Start the app: `python app.py`
10. Log in → confirm each row has an Edit button.
11. Click Edit on a row → confirm modal opens with correct pre-filled values.
12. Change a value → Save → confirm table shows the updated value.
13. Submit with an empty field → confirm error appears and modal re-opens.
14. Confirm all SQL uses `?` placeholders — search for f-strings in `edit_expense`.
