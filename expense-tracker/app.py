import os
from flask import Flask, render_template, request, redirect, url_for, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, close_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
app.config['DATABASE'] = os.path.join(app.root_path, 'expense_tracker.db')
app.teardown_appcontext(close_db)


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not name or not email or not password:
            return render_template("register.html", error="All fields are required.")
        if len(password) < 4:
            return render_template("register.html", error="Password must be at least 4 characters.")

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return render_template("register.html", error="An account with that email already exists.")

        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password))
        )
        db.commit()
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            return render_template("login.html", error="Please enter your email and password.")

        db   = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.")

        session["user_id"]   = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("profile"))

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    from datetime import datetime
    from collections import defaultdict

    user_id = session["user_id"]
    db = get_db()

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


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)
