"""
Tests for Step 7 — Add Expense GUI.

These tests are spec-driven: they verify what POST /expenses/add SHOULD do
(HTTP contract, DB writes, redirects, validation errors) regardless of how
the implementation is written internally.
"""

import os
import tempfile
import pytest
from urllib.parse import urlparse, parse_qs
from werkzeug.security import generate_password_hash

from app import app as flask_app
from database.db import get_db, init_db


# ------------------------------------------------------------------ #
# Fixtures                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture
def app():
    """Create the Flask app backed by a fresh temp-file SQLite DB per test."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    flask_app.config.update({
        "TESTING": True,
        "DATABASE": db_path,
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
    })
    with flask_app.app_context():
        init_db()
        _seed_test_user()
    yield flask_app
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Return a Flask test client."""
    return app.test_client()


@pytest.fixture
def logged_in_client(client):
    """Return a test client already authenticated as the seeded test user."""
    _login(client, TEST_EMAIL, TEST_PASSWORD)
    return client


# ------------------------------------------------------------------ #
# Seed helpers                                                        #
# ------------------------------------------------------------------ #

TEST_EMAIL = "addexpense@example.com"
TEST_PASSWORD = "testpass"


def _seed_test_user():
    """Insert a single test user into the DB (call inside an app context)."""
    db = get_db()
    db.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        ("Test User", TEST_EMAIL, generate_password_hash(TEST_PASSWORD), "2026-01-01 00:00:00"),
    )
    db.commit()


def _login(client, email, password):
    """POST to /login with the given credentials and return the response."""
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


def _post_add_expense(client, data, follow_redirects=False):
    """POST form data to /expenses/add and return the response."""
    return client.post(
        "/expenses/add",
        data=data,
        follow_redirects=follow_redirects,
    )


def _count_expenses_for_user(app, email):
    """Return the total number of expense rows owned by the given user."""
    with app.app_context():
        db = get_db()
        user = db.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        if user is None:
            return 0
        return db.execute(
            "SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user["id"],)
        ).fetchone()[0]


def _get_latest_expense(app, email):
    """Return the most recently inserted expense dict for the user, or None."""
    with app.app_context():
        db = get_db()
        user = db.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        if user is None:
            return None
        row = db.execute(
            "SELECT * FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user["id"],)
        ).fetchone()
        return dict(row) if row else None


# ------------------------------------------------------------------ #
# Auth guard — unauthenticated access                                 #
# ------------------------------------------------------------------ #

def test_post_add_expense_unauthenticated_redirects_to_login(client):
    """Unauthenticated POST /expenses/add must redirect to /login."""
    response = _post_add_expense(client, {
        "amount": "500",
        "category": "Food",
        "date": "2026-07-01",
        "description": "Lunch",
    })
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_get_add_expense_unauthenticated_redirects_to_login(client):
    """Unauthenticated GET /expenses/add must redirect to /login."""
    response = client.get("/expenses/add")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# ------------------------------------------------------------------ #
# GET /expenses/add — logged-in user                                  #
# ------------------------------------------------------------------ #

def test_get_add_expense_authenticated_redirects_to_profile(logged_in_client):
    """Authenticated GET /expenses/add must silently redirect to /profile."""
    response = logged_in_client.get("/expenses/add")
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]


def test_get_add_expense_does_not_insert_into_db(app, logged_in_client):
    """A GET request to /expenses/add must not write any expense row to the DB."""
    before = _count_expenses_for_user(app, TEST_EMAIL)
    logged_in_client.get("/expenses/add")
    after = _count_expenses_for_user(app, TEST_EMAIL)
    assert after == before


# ------------------------------------------------------------------ #
# Happy path — valid POST                                             #
# ------------------------------------------------------------------ #

def test_valid_post_add_expense_redirects_to_profile(logged_in_client):
    """A valid form POST must redirect to /profile on success."""
    response = _post_add_expense(logged_in_client, {
        "amount": "500",
        "category": "Food",
        "date": "2026-07-01",
        "description": "Grocery run",
    })
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]


def test_valid_post_add_expense_inserts_one_row_into_db(app, logged_in_client):
    """A valid form POST must insert exactly one new expense row into the DB."""
    before = _count_expenses_for_user(app, TEST_EMAIL)
    _post_add_expense(logged_in_client, {
        "amount": "1200",
        "category": "Travel",
        "date": "2026-06-15",
        "description": "Train ticket",
    })
    after = _count_expenses_for_user(app, TEST_EMAIL)
    assert after == before + 1


def test_valid_post_stores_correct_amount_in_db(app, logged_in_client):
    """The inserted expense must store the correct amount value."""
    _post_add_expense(logged_in_client, {
        "amount": "750.50",
        "category": "Bills",
        "date": "2026-07-10",
        "description": "Electricity",
    })
    expense = _get_latest_expense(app, TEST_EMAIL)
    assert expense is not None
    assert expense["amount"] == pytest.approx(750.50)


def test_valid_post_stores_correct_category_in_db(app, logged_in_client):
    """The inserted expense must store the correct category string."""
    _post_add_expense(logged_in_client, {
        "amount": "300",
        "category": "Shopping",
        "date": "2026-07-05",
        "description": "New shoes",
    })
    expense = _get_latest_expense(app, TEST_EMAIL)
    assert expense is not None
    assert expense["category"] == "Shopping"


def test_valid_post_stores_correct_date_in_db(app, logged_in_client):
    """The inserted expense must store the exact YYYY-MM-DD date string."""
    _post_add_expense(logged_in_client, {
        "amount": "200",
        "category": "Health",
        "date": "2026-07-20",
        "description": "Pharmacy",
    })
    expense = _get_latest_expense(app, TEST_EMAIL)
    assert expense is not None
    assert expense["date"] == "2026-07-20"


def test_valid_post_stores_correct_description_in_db(app, logged_in_client):
    """The inserted expense must store the provided description text."""
    _post_add_expense(logged_in_client, {
        "amount": "450",
        "category": "Food",
        "date": "2026-07-12",
        "description": "Restaurant dinner",
    })
    expense = _get_latest_expense(app, TEST_EMAIL)
    assert expense is not None
    assert expense["description"] == "Restaurant dinner"


def test_valid_post_redirect_location_does_not_contain_add_error(logged_in_client):
    """A successful submission must not include add_error in the redirect URL."""
    response = _post_add_expense(logged_in_client, {
        "amount": "100",
        "category": "Other",
        "date": "2026-07-01",
    })
    assert "add_error" not in response.headers.get("Location", "")


def test_valid_post_fractional_amount_is_accepted(logged_in_client):
    """A decimal amount like 149.99 must be accepted and redirect to /profile."""
    response = _post_add_expense(logged_in_client, {
        "amount": "149.99",
        "category": "Food",
        "date": "2026-07-01",
    })
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]
    assert "add_error" not in response.headers.get("Location", "")


# ------------------------------------------------------------------ #
# Description field — optional                                        #
# ------------------------------------------------------------------ #

def test_post_add_expense_without_description_field_succeeds(logged_in_client):
    """Omitting the description key entirely must still save the expense successfully."""
    response = _post_add_expense(logged_in_client, {
        "amount": "500",
        "category": "Food",
        "date": "2026-07-01",
    })
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]


def test_post_add_expense_blank_description_stored_as_null(app, logged_in_client):
    """A blank description string must be stored as NULL (None) in the DB."""
    _post_add_expense(logged_in_client, {
        "amount": "500",
        "category": "Entertainment",
        "date": "2026-07-01",
        "description": "",
    })
    expense = _get_latest_expense(app, TEST_EMAIL)
    assert expense is not None
    assert expense["description"] is None


def test_post_add_expense_no_description_key_stored_as_null(app, logged_in_client):
    """When no description key is submitted at all, the DB must store NULL."""
    _post_add_expense(logged_in_client, {
        "amount": "250",
        "category": "Health",
        "date": "2026-07-03",
    })
    expense = _get_latest_expense(app, TEST_EMAIL)
    assert expense is not None
    assert expense["description"] is None


# ------------------------------------------------------------------ #
# Validation — missing required fields                                #
# ------------------------------------------------------------------ #

def test_post_missing_amount_redirects_with_add_error(logged_in_client):
    """Submitting without 'amount' must redirect to /profile with add_error in the URL."""
    response = _post_add_expense(logged_in_client, {
        "category": "Food",
        "date": "2026-07-01",
    })
    assert response.status_code == 302
    location = response.headers.get("Location", "")
    assert "/profile" in location
    assert "add_error" in location


def test_post_missing_category_redirects_with_add_error(logged_in_client):
    """Submitting without 'category' must redirect to /profile with add_error in the URL."""
    response = _post_add_expense(logged_in_client, {
        "amount": "500",
        "date": "2026-07-01",
    })
    assert response.status_code == 302
    location = response.headers.get("Location", "")
    assert "/profile" in location
    assert "add_error" in location


def test_post_missing_date_redirects_with_add_error(logged_in_client):
    """Submitting without 'date' must redirect to /profile with add_error in the URL."""
    response = _post_add_expense(logged_in_client, {
        "amount": "500",
        "category": "Food",
    })
    assert response.status_code == 302
    location = response.headers.get("Location", "")
    assert "/profile" in location
    assert "add_error" in location


def test_post_empty_amount_string_redirects_with_add_error(logged_in_client):
    """An empty-string amount must redirect to /profile with add_error."""
    response = _post_add_expense(logged_in_client, {
        "amount": "",
        "category": "Food",
        "date": "2026-07-01",
    })
    assert response.status_code == 302
    assert "add_error" in response.headers.get("Location", "")


def test_post_empty_category_string_redirects_with_add_error(logged_in_client):
    """An empty-string category must redirect to /profile with add_error."""
    response = _post_add_expense(logged_in_client, {
        "amount": "500",
        "category": "",
        "date": "2026-07-01",
    })
    assert response.status_code == 302
    assert "add_error" in response.headers.get("Location", "")


def test_post_empty_date_string_redirects_with_add_error(logged_in_client):
    """An empty-string date must redirect to /profile with add_error."""
    response = _post_add_expense(logged_in_client, {
        "amount": "500",
        "category": "Food",
        "date": "",
    })
    assert response.status_code == 302
    assert "add_error" in response.headers.get("Location", "")


@pytest.mark.parametrize("missing_field,data", [
    ("amount",   {"category": "Food",    "date": "2026-07-01"}),
    ("category", {"amount": "500",       "date": "2026-07-01"}),
    ("date",     {"amount": "500",       "category": "Food"}),
])
def test_post_missing_required_field_does_not_insert_into_db(
    app, logged_in_client, missing_field, data
):
    """Missing any required field must not write a new expense to the DB."""
    before = _count_expenses_for_user(app, TEST_EMAIL)
    _post_add_expense(logged_in_client, data)
    after = _count_expenses_for_user(app, TEST_EMAIL)
    assert after == before, f"DB row was inserted despite missing required field '{missing_field}'"


# ------------------------------------------------------------------ #
# Validation — invalid amount                                         #
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("bad_amount", ["0", "0.00", "-1", "-500", "-0.01"])
def test_post_non_positive_amount_redirects_with_add_error(logged_in_client, bad_amount):
    """A zero or negative amount must redirect to /profile with add_error."""
    response = _post_add_expense(logged_in_client, {
        "amount": bad_amount,
        "category": "Food",
        "date": "2026-07-01",
    })
    assert response.status_code == 302
    assert "add_error" in response.headers.get("Location", "")


@pytest.mark.parametrize("non_numeric", ["abc", "one hundred", "rupees", "5 00", "5,00"])
def test_post_non_numeric_amount_redirects_with_add_error(logged_in_client, non_numeric):
    """A non-numeric amount string must redirect to /profile with add_error."""
    response = _post_add_expense(logged_in_client, {
        "amount": non_numeric,
        "category": "Food",
        "date": "2026-07-01",
    })
    assert response.status_code == 302
    assert "add_error" in response.headers.get("Location", "")


@pytest.mark.parametrize("bad_amount", ["0", "-1", "abc", "five"])
def test_post_invalid_amount_does_not_insert_into_db(app, logged_in_client, bad_amount):
    """Invalid amount values must never write a row to the expenses table."""
    before = _count_expenses_for_user(app, TEST_EMAIL)
    _post_add_expense(logged_in_client, {
        "amount": bad_amount,
        "category": "Food",
        "date": "2026-07-01",
    })
    after = _count_expenses_for_user(app, TEST_EMAIL)
    assert after == before


# ------------------------------------------------------------------ #
# Validation — invalid date format                                    #
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("bad_date", [
    "01-07-2026",    # DD-MM-YYYY — wrong order and separator
    "2026/07/01",    # slashes instead of hyphens
    "July 1 2026",   # text month
    "20260701",      # no separators at all
    "not-a-date",    # gibberish
    "2026-13-01",    # month 13 — out of range
    "2026-07-32",    # day 32 — out of range
])
def test_post_invalid_date_format_redirects_with_add_error(logged_in_client, bad_date):
    """An invalidly-formatted date must redirect to /profile with add_error."""
    response = _post_add_expense(logged_in_client, {
        "amount": "500",
        "category": "Food",
        "date": bad_date,
    })
    assert response.status_code == 302
    assert "add_error" in response.headers.get("Location", "")


@pytest.mark.parametrize("bad_date", ["01-07-2026", "not-a-date", "2026-13-01"])
def test_post_invalid_date_does_not_insert_into_db(app, logged_in_client, bad_date):
    """An invalid date format must never write a row to the expenses table."""
    before = _count_expenses_for_user(app, TEST_EMAIL)
    _post_add_expense(logged_in_client, {
        "amount": "500",
        "category": "Food",
        "date": bad_date,
    })
    after = _count_expenses_for_user(app, TEST_EMAIL)
    assert after == before


# ------------------------------------------------------------------ #
# Validation error redirect — modal re-open via query param           #
# ------------------------------------------------------------------ #

def test_validation_error_redirect_location_contains_add_error_param(logged_in_client):
    """On validation failure the Location header must contain 'add_error=' in its query string."""
    response = _post_add_expense(logged_in_client, {
        "amount": "-99",
        "category": "Food",
        "date": "2026-07-01",
    })
    location = response.headers.get("Location", "")
    assert "add_error=" in location


def test_following_validation_error_redirect_renders_error_message(logged_in_client):
    """Following the validation redirect must render the error text in the profile page body."""
    response = _post_add_expense(logged_in_client, {
        "amount": "0",
        "category": "Food",
        "date": "2026-07-01",
    }, follow_redirects=True)
    body = response.data.decode()
    # The spec error text is "Amount must be a positive number."
    assert "positive" in body.lower() or "amount" in body.lower()


def test_profile_with_add_error_query_param_renders_200(logged_in_client):
    """GET /profile?add_error=... must return HTTP 200 without crashing."""
    response = logged_in_client.get(
        "/profile?add_error=Amount+must+be+a+positive+number."
    )
    assert response.status_code == 200


def test_profile_with_add_error_query_param_shows_error_text(logged_in_client):
    """GET /profile?add_error=<msg> must render the error message in the page body."""
    response = logged_in_client.get(
        "/profile?add_error=Amount+must+be+a+positive+number."
    )
    body = response.data.decode()
    assert "positive" in body.lower() or "amount" in body.lower()


def test_profile_with_add_error_includes_modal_open_call(logged_in_client):
    """When add_error is present, the profile page must include openModal() in the JS block."""
    response = logged_in_client.get(
        "/profile?add_error=Amount+must+be+a+positive+number."
    )
    body = response.data.decode()
    assert "openModal" in body


def test_profile_without_add_error_does_not_include_modal_open_call(logged_in_client):
    """When no add_error is in the URL, the profile page must NOT auto-call openModal()."""
    response = logged_in_client.get("/profile")
    body = response.data.decode()
    # The auto-open call should be absent; the modal JS definition itself may still be present
    # We look for the specific conditional invocation pattern from the spec
    assert "openModal();" not in body


# ------------------------------------------------------------------ #
# Profile page renders after expense is added                         #
# ------------------------------------------------------------------ #

def test_profile_renders_without_crash_after_expense_added(logged_in_client):
    """GET /profile must return HTTP 200 after at least one expense has been inserted."""
    _post_add_expense(logged_in_client, {
        "amount": "600",
        "category": "Food",
        "date": "2026-07-01",
        "description": "Dinner",
    })
    response = logged_in_client.get("/profile")
    assert response.status_code == 200


def test_profile_total_spent_stat_updates_after_expense_added(logged_in_client):
    """The total-spent stat on /profile must reflect the amount of the newly added expense."""
    _post_add_expense(logged_in_client, {
        "amount": "1234",
        "category": "Travel",
        "date": "2026-07-15",
        "description": "Flight",
    })
    response = logged_in_client.get("/profile")
    body = response.data.decode()
    assert "1,234" in body


def test_profile_new_expense_description_appears_in_transaction_list(logged_in_client):
    """The description of a newly added expense must appear in the profile transaction list."""
    _post_add_expense(logged_in_client, {
        "amount": "800",
        "category": "Shopping",
        "date": "2026-07-10",
        "description": "Unique laptop bag purchase",
    })
    response = logged_in_client.get("/profile")
    body = response.data.decode()
    assert "Unique laptop bag purchase" in body


def test_profile_new_expense_category_appears_after_insert(logged_in_client):
    """The category of a newly added expense must appear in the profile page."""
    _post_add_expense(logged_in_client, {
        "amount": "450",
        "category": "Entertainment",
        "date": "2026-07-08",
        "description": "Concert tickets",
    })
    response = logged_in_client.get("/profile")
    body = response.data.decode()
    assert "Entertainment" in body


def test_profile_top_category_updates_to_reflect_added_expense(logged_in_client):
    """Top category stat must update to reflect the category of the newly inserted expense."""
    _post_add_expense(logged_in_client, {
        "amount": "9999",
        "category": "Health",
        "date": "2026-07-01",
        "description": "Hospital bill",
    })
    response = logged_in_client.get("/profile")
    body = response.data.decode()
    assert "Health" in body


def test_profile_transaction_count_increments_after_each_add(logged_in_client):
    """Transaction count stat must increase by 1 for each expense successfully added."""
    _post_add_expense(logged_in_client, {
        "amount": "100",
        "category": "Other",
        "date": "2026-07-01",
    })
    _post_add_expense(logged_in_client, {
        "amount": "200",
        "category": "Bills",
        "date": "2026-07-02",
    })
    response = logged_in_client.get("/profile")
    assert response.status_code == 200
    # Two expenses are present; the page must not crash and must show numeric count
    body = response.data.decode()
    assert "2" in body


# ------------------------------------------------------------------ #
# Profile page — add-expense form elements present                    #
# ------------------------------------------------------------------ #

def test_profile_contains_add_expense_button(logged_in_client):
    """The profile page must render a visible 'Add Expense' button for logged-in users."""
    response = logged_in_client.get("/profile")
    body = response.data.decode()
    assert "Add Expense" in body


def test_profile_add_expense_form_posts_to_expenses_add(logged_in_client):
    """The add-expense form's action must point to /expenses/add."""
    response = logged_in_client.get("/profile")
    body = response.data.decode()
    assert "/expenses/add" in body


def test_profile_add_expense_form_has_amount_input(logged_in_client):
    """The add-expense form must include an input field named 'amount'."""
    response = logged_in_client.get("/profile")
    assert 'name="amount"' in response.data.decode()


def test_profile_add_expense_form_has_category_select(logged_in_client):
    """The add-expense form must include a select element named 'category'."""
    response = logged_in_client.get("/profile")
    assert 'name="category"' in response.data.decode()


def test_profile_add_expense_form_has_date_input(logged_in_client):
    """The add-expense form must include an input field named 'date'."""
    response = logged_in_client.get("/profile")
    assert 'name="date"' in response.data.decode()


def test_profile_add_expense_form_has_description_input(logged_in_client):
    """The add-expense form must include an optional input field named 'description'."""
    response = logged_in_client.get("/profile")
    assert 'name="description"' in response.data.decode()


@pytest.mark.parametrize("category", [
    "Food", "Travel", "Bills", "Shopping", "Entertainment", "Health", "Other"
])
def test_profile_category_dropdown_contains_all_valid_options(logged_in_client, category):
    """The add-expense category dropdown must include every allowed category from the spec."""
    response = logged_in_client.get("/profile")
    body = response.data.decode()
    assert category in body, f"Category option '{category}' is missing from the add-expense form"


# ------------------------------------------------------------------ #
# User data isolation                                                 #
# ------------------------------------------------------------------ #

def test_add_expense_associates_row_with_authenticated_user_only(app, logged_in_client):
    """An inserted expense must be owned by the current user, not any other account."""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            ("Other User", "other2@example.com", generate_password_hash("pass"), "2026-01-01 00:00:00"),
        )
        db.commit()

    _post_add_expense(logged_in_client, {
        "amount": "777",
        "category": "Other",
        "date": "2026-07-01",
        "description": "Belongs to test user only",
    })

    with app.app_context():
        db = get_db()
        other = db.execute(
            "SELECT id FROM users WHERE email = ?", ("other2@example.com",)
        ).fetchone()
        other_count = db.execute(
            "SELECT COUNT(*) FROM expenses WHERE user_id = ?", (other["id"],)
        ).fetchone()[0]
    assert other_count == 0


def test_second_user_cannot_see_expense_added_by_first_user(app, logged_in_client):
    """An expense added by one user must not appear on another user's profile page."""
    _post_add_expense(logged_in_client, {
        "amount": "888",
        "category": "Food",
        "date": "2026-07-01",
        "description": "Secret snack",
    })

    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            ("Bystander", "bystander@example.com", generate_password_hash("bypassword"), "2026-01-01 00:00:00"),
        )
        db.commit()

    other_client = app.test_client()
    _login(other_client, "bystander@example.com", "bypassword")
    response = other_client.get("/profile")
    body = response.data.decode()
    assert "Secret snack" not in body
    assert "888" not in body
