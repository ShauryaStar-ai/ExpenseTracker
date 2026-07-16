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
