# Spec — Step 9: Delete Expense on Profile Page

## 1. Overview

Add a **Delete** button to each row in the transactions table on `/profile`.
Clicking it shows a small inline confirmation (no full-page redirect) before
sending a `POST /expenses/<id>/delete` request.  The route validates ownership,
deletes the record, and redirects back to `/profile`.

The Delete button sits alongside the existing Edit button introduced in Step 8,
reusing `.row-actions` and the same ownership-check pattern.

---

## 2. Depends on

- **Step 8 (Edit Expense)** — the Actions column (`.row-actions`, `.btn-row-edit`)
  and the `id` field in each `transactions` dict must already exist.
- **Step 3 (Login / Logout)** — `session['user_id']` must be set for auth guard.

---

## 3. Route change

### `POST /expenses/<int:id>/delete` *(replace stub)*

| Item | Detail |
| --- | --- |
| URL | `/expenses/<id>/delete` |
| Methods | `POST` |
| Auth | Redirect to `/login` if `session['user_id']` is not set |
| Ownership check | Fetch the expense; if not found or `user_id` ≠ session → `abort(403)` |
| `GET` | Redirect to `/profile` (no standalone delete page) |
| `POST` success | Delete record, redirect to `url_for('profile')` |

> **Why POST?** Deletes must use a form POST, not a bare `<a href>` GET link.
> A GET link would let browsers and link-prefetchers silently delete data.

---

## 4. Database

No schema changes.  The `expenses` table already has `id` and `user_id`.

---

## 5. Backend — `app.py`

### 5a. Full replacement for `delete_expense()`

Replace the stub at line 294 with:

```python
@app.route("/expenses/<int:id>/delete", methods=["GET", "POST"])
def delete_expense(id):
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

    db.execute("DELETE FROM expenses WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("profile"))
```

No changes to `profile()` are needed — `id` is already in every transaction dict
from Step 8.

---

## 6. Template changes — `profile.html`

### 6a. Add Delete button to the Actions column

Inside `.row-actions`, add a Delete form **after** the existing Edit button:

```html
<td class="row-actions">
  <button class="btn-row-edit"
          data-id="{{ t.id }}"
          data-amount="{{ t.amount_raw }}"
          data-category="{{ t.category }}"
          data-date="{{ t.date_raw }}"
          data-description="{{ t.description }}"
          aria-label="Edit expense">Edit</button>

  <form class="delete-form"
        method="post"
        action="{{ url_for('delete_expense', id=t.id) }}"
        data-description="{{ t.description or t.category }}">
    <button type="button" class="btn-row-delete"
            aria-label="Delete expense">Delete</button>
  </form>
</td>
```

### 6b. Confirmation overlay (inline)

Add a single shared confirmation overlay near the bottom of the page, just
before the Add Expense modal:

```html
<!-- Delete confirmation overlay -->
<div class="modal-overlay" id="delete-confirm-modal" role="dialog"
     aria-modal="true" aria-labelledby="delete-confirm-title">
  <div class="modal-card modal-card--sm">
    <div class="modal-header">
      <h2 class="modal-title" id="delete-confirm-title">Delete Expense</h2>
      <button class="modal-close" id="close-delete-confirm"
              aria-label="Close">&times;</button>
    </div>
    <p class="delete-confirm-msg">
      Are you sure you want to delete
      <strong id="delete-confirm-desc"></strong>?
      This cannot be undone.
    </p>
    <div class="form-actions">
      <button id="confirm-delete-btn" class="btn btn-danger">Delete</button>
      <button id="cancel-delete-btn" class="btn btn-ghost">Cancel</button>
    </div>
  </div>
</div>
```

### 6c. JavaScript — append to the existing `{% block scripts %}`

Add after the edit modal JS block:

```javascript
const deleteOverlay      = document.getElementById('delete-confirm-modal');
const closeDeleteBtn     = document.getElementById('close-delete-confirm');
const cancelDeleteBtn    = document.getElementById('cancel-delete-btn');
const confirmDeleteBtn   = document.getElementById('confirm-delete-btn');
const deleteConfirmDesc  = document.getElementById('delete-confirm-desc');

let pendingDeleteForm = null;

function openDeleteConfirm(form) {
  pendingDeleteForm = form;
  deleteConfirmDesc.textContent = form.dataset.description || 'this expense';
  deleteOverlay.classList.add('modal-visible');
}
function closeDeleteConfirm() {
  pendingDeleteForm = null;
  deleteOverlay.classList.remove('modal-visible');
}

closeDeleteBtn.addEventListener('click', closeDeleteConfirm);
cancelDeleteBtn.addEventListener('click', closeDeleteConfirm);
deleteOverlay.addEventListener('click', (e) => {
  if (e.target === deleteOverlay) closeDeleteConfirm();
});

confirmDeleteBtn.addEventListener('click', () => {
  if (pendingDeleteForm) pendingDeleteForm.submit();
});

document.querySelectorAll('.btn-row-delete').forEach(btn => {
  btn.addEventListener('click', () => {
    openDeleteConfirm(btn.closest('.delete-form'));
  });
});
```

---

## 7. CSS additions — `static/css/style.css`

Append at the end of the file:

```css
/* ── Delete button ─────────────────────────────── */
.btn-row-delete {
  font-size: 0.8rem;
  padding: 0.2rem 0.6rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--paper-card);
  color: #c0392b;
  cursor: pointer;
  font-weight: 600;
}

.btn-row-delete:hover {
  background: #c0392b;
  color: #fff;
  border-color: #c0392b;
}

.delete-form {
  display: inline;
}

/* ── Danger button variant ─────────────────────── */
.btn-danger {
  background: #c0392b;
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  padding: 0.55rem 1.25rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-danger:hover {
  background: #a93226;
}

/* ── Small modal card variant ──────────────────── */
.modal-card--sm {
  max-width: 400px;
}

.delete-confirm-msg {
  margin: 0.5rem 0 1.25rem;
  line-height: 1.5;
}
```

---

## 8. Files to Change

| File | Action |
| --- | --- |
| `expense-tracker/app.py` | Replace `delete_expense()` stub with full handler |
| `expense-tracker/templates/profile.html` | Add Delete button + form inside `.row-actions`; add confirmation overlay; extend JS block |
| `expense-tracker/static/css/style.css` | Append Delete button + danger btn + small modal CSS |

## 9. Files to Create

None.

---

## 10. Edge Cases

| Scenario | Expected behaviour |
| --- | --- |
| User tries to delete another user's expense | `abort(403)` — Flask returns a 403 page |
| Expense ID does not exist | `abort(403)` — same path (no info leak) |
| GET `/expenses/<id>/delete` | Redirect to `/profile` (no direct deletion via URL) |
| User clicks Cancel in confirmation modal | Modal closes; no form submitted; no data changed |
| No expenses on profile | No Delete buttons rendered; no JS errors |
| Filter is active when Delete is clicked | Delete still works; after redirect the filter resets (same as edit expense) |
| User deletes the last expense | Profile renders with empty table and zeroed stats; no crash |

---

## 11. Definition of Done

- [ ] Each row in the transactions table has a Delete button next to the Edit button
- [ ] Clicking Delete opens the confirmation modal with the expense description
- [ ] Clicking Cancel in the modal closes it without deleting anything
- [ ] Clicking Delete in the modal submits the form and removes the record from the DB
- [ ] After deletion the page reloads and the deleted row is no longer visible
- [ ] Stats (total spent, count, top category) reflect the deletion
- [ ] A user cannot delete another user's expense (403 response)
- [ ] GET `/expenses/<id>/delete` redirects to `/profile` (no standalone page)
- [ ] All SQL uses `?` placeholders — no f-strings in SQL
- [ ] Deleting the last expense leaves an empty table with no crash

---

## 12. Implementation Order

1. Replace the `delete_expense()` stub in `app.py` with the full handler.
2. Add the Delete form + button inside `.row-actions` in `profile.html`.
3. Add the confirmation modal HTML to `profile.html`.
4. Append the delete JS block to the `{% block scripts %}` section.
5. Append Delete + danger button + small modal CSS to `style.css`.
6. Start the app: `python app.py`
7. Log in → confirm each row shows both Edit and Delete buttons.
8. Click Delete → confirm the confirmation modal appears with the right description.
9. Click Cancel → confirm modal closes and row still exists.
10. Click Delete again → confirm → confirm row disappears and stats update.
11. Confirm a GET request to `/expenses/<id>/delete` redirects to `/profile`.
12. Confirm all SQL uses `?` placeholders — search for f-strings in `delete_expense`.
