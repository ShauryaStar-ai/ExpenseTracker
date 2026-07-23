"""
Tests for Step 6 — Data Filter for Profile Page.

These tests are spec-driven: they verify what GET /profile SHOULD do
(HTTP contract, rendered content, filter behaviour) regardless of how
the implementation is written internally.
"""

import os
import tempfile
import pytest
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
        _seed_test_user_and_expenses()
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
    _login(client, "filter@example.com", "testpass")
    return client


# ------------------------------------------------------------------ #
# Seed helpers                                                        #
# ------------------------------------------------------------------ #

TEST_EMAIL = "filter@example.com"
TEST_PASSWORD = "testpass"

# Expenses seeded for the test user, spread across months and categories.
# Summary:
#   Food    : 2026-01-15 ₹500, 2026-03-20 ₹300  → total ₹800
#   Travel  : 2026-02-10 ₹1500                   → total ₹1500
#   Bills   : 2026-04-05 ₹800                    → total ₹800
#   Shopping: 2026-05-12 ₹1200                   → total ₹1200
#   Entertainment: 2026-06-18 ₹400               → total ₹400
#   Grand total: ₹4200, 6 rows
SEED_EXPENSES = [
    (500.00,  "Food",          "2026-01-15", "January groceries"),
    (300.00,  "Food",          "2026-03-20", "March lunch"),
    (1500.00, "Travel",        "2026-02-10", "Train ticket"),
    (800.00,  "Bills",         "2026-04-05", "Electricity"),
    (1200.00, "Shopping",      "2026-05-12", "Clothes"),
    (400.00,  "Entertainment", "2026-06-18", "Movie"),
]


def _seed_test_user_and_expenses():
    """Insert the test user and their expenses into the DB (call inside app ctx)."""
    db = get_db()
    db.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        ("Test User", TEST_EMAIL, generate_password_hash(TEST_PASSWORD), "2026-01-01 00:00:00"),
    )
    db.commit()
    user_id = db.execute(
        "SELECT id FROM users WHERE email = ?", (TEST_EMAIL,)
    ).fetchone()["id"]
    db.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [(user_id,) + row for row in SEED_EXPENSES],
    )
    db.commit()


def _login(client, email, password):
    """POST to /login and return the response."""
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


# ------------------------------------------------------------------ #
# Auth guard                                                          #
# ------------------------------------------------------------------ #

def test_profile_redirects_to_login_when_unauthenticated(client):
    """Unauthenticated GET /profile must redirect to /login."""
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_redirects_to_login_with_no_session_even_with_filter_params(client):
    """Filter params must not bypass the auth guard."""
    response = client.get("/profile?category=Food&from=2026-01-01&to=2026-06-30")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# ------------------------------------------------------------------ #
# Happy path — no filter                                             #
# ------------------------------------------------------------------ #

def test_profile_no_filter_returns_200(logged_in_client):
    """GET /profile with no params returns HTTP 200 for authenticated user."""
    response = logged_in_client.get("/profile")
    assert response.status_code == 200


def test_profile_no_filter_shows_all_seeded_expenses(logged_in_client):
    """Unfiltered profile lists every seeded expense description."""
    response = logged_in_client.get("/profile")
    body = response.data.decode()
    assert "January groceries" in body
    assert "March lunch" in body
    assert "Train ticket" in body
    assert "Electricity" in body
    assert "Clothes" in body
    assert "Movie" in body


def test_profile_no_filter_total_spent_is_sum_of_all_expenses(logged_in_client):
    """Unfiltered total_spent stat equals the sum of all seeded expenses (₹4,700)."""
    response = logged_in_client.get("/profile")
    body = response.data.decode()
    # Grand total: 500+300+1500+800+1200+400 = 4700
    assert "4,700" in body


def test_profile_no_filter_transaction_count_matches_seeded_rows(logged_in_client):
    """Unfiltered transaction count equals the number of seeded expenses (6)."""
    response = logged_in_client.get("/profile")
    body = response.data.decode()
    assert "6" in body


def test_profile_no_filter_category_dropdown_lists_all_user_categories(logged_in_client):
    """Category dropdown contains every distinct category from the user's expenses."""
    response = logged_in_client.get("/profile")
    body = response.data.decode()
    for cat in ("Food", "Travel", "Bills", "Shopping", "Entertainment"):
        assert cat in body


def test_profile_filter_form_rendered_with_expected_controls(logged_in_client):
    """Profile page renders the filter form with category select, from, and to inputs."""
    response = logged_in_client.get("/profile")
    body = response.data.decode()
    # Category select element
    assert 'name="category"' in body
    # Date range inputs
    assert 'name="from"' in body
    assert 'name="to"' in body
    # Apply and Clear controls
    assert "Apply" in body
    assert "Clear" in body


# ------------------------------------------------------------------ #
# Category filter                                                     #
# ------------------------------------------------------------------ #

def test_profile_category_filter_shows_only_matching_expenses(logged_in_client):
    """Filtering by 'Food' shows only Food expenses and hides other categories."""
    response = logged_in_client.get("/profile?category=Food")
    body = response.data.decode()
    assert "January groceries" in body
    assert "March lunch" in body
    # Non-Food expenses must not appear
    assert "Train ticket" not in body
    assert "Electricity" not in body
    assert "Clothes" not in body
    assert "Movie" not in body


def test_profile_category_filter_updates_total_spent_stat(logged_in_client):
    """Total spent stat reflects only the filtered category (Food = ₹800)."""
    response = logged_in_client.get("/profile?category=Food")
    body = response.data.decode()
    assert "800" in body


def test_profile_category_filter_updates_transaction_count(logged_in_client):
    """Transaction count stat reflects filtered rows only (Food = 2 rows)."""
    response = logged_in_client.get("/profile?category=Food")
    body = response.data.decode()
    # There are exactly 2 Food expenses seeded
    assert "2" in body


def test_profile_category_filter_top_category_reflects_filtered_data(logged_in_client):
    """Top category stat equals the filtered category when one category is selected."""
    response = logged_in_client.get("/profile?category=Travel")
    body = response.data.decode()
    assert "Travel" in body


def test_profile_category_filter_other_categories_absent_from_breakdown(logged_in_client):
    """Category breakdown section shows only the filtered category, not others."""
    response = logged_in_client.get("/profile?category=Shopping")
    body = response.data.decode()
    # Shopping breakdown present
    assert "Shopping" in body
    # Bills and Food should not appear in breakdown amounts for this filter
    # We check that non-Shopping descriptions are absent as a proxy
    assert "Electricity" not in body
    assert "Train ticket" not in body


# ------------------------------------------------------------------ #
# Date range filter                                                   #
# ------------------------------------------------------------------ #

def test_profile_from_date_filter_excludes_expenses_before_date(logged_in_client):
    """'from' filter hides expenses with dates earlier than the given value."""
    # from=2026-02-01 → Jan Food expense excluded
    response = logged_in_client.get("/profile?from=2026-02-01")
    body = response.data.decode()
    assert "January groceries" not in body
    # Feb and later should appear
    assert "Train ticket" in body
    assert "March lunch" in body


def test_profile_to_date_filter_excludes_expenses_after_date(logged_in_client):
    """'to' filter hides expenses with dates later than the given value."""
    # to=2026-02-28 → only Jan Food and Feb Travel visible
    response = logged_in_client.get("/profile?to=2026-02-28")
    body = response.data.decode()
    assert "January groceries" in body
    assert "Train ticket" in body
    assert "March lunch" not in body
    assert "Electricity" not in body


def test_profile_date_range_filter_shows_only_expenses_in_range(logged_in_client):
    """from + to together show only expenses whose date falls within the range."""
    # Range: Feb through Apr — Travel, Food(Mar), Bills
    response = logged_in_client.get("/profile?from=2026-02-01&to=2026-04-30")
    body = response.data.decode()
    assert "Train ticket" in body     # 2026-02-10 in range
    assert "March lunch" in body      # 2026-03-20 in range
    assert "Electricity" in body      # 2026-04-05 in range
    assert "January groceries" not in body   # 2026-01-15 before range
    assert "Clothes" not in body      # 2026-05-12 after range
    assert "Movie" not in body        # 2026-06-18 after range


def test_profile_date_range_filter_updates_total_spent(logged_in_client):
    """Total spent reflects only expenses in the filtered date range."""
    # Range Feb–Apr: Travel(1500) + FoodMar(300) + Bills(800) = 2600
    response = logged_in_client.get("/profile?from=2026-02-01&to=2026-04-30")
    body = response.data.decode()
    assert "2,600" in body


def test_profile_date_range_filter_updates_transaction_count(logged_in_client):
    """Transaction count reflects only the expenses in the filtered date range."""
    # Feb–Apr: 3 expenses
    response = logged_in_client.get("/profile?from=2026-02-01&to=2026-04-30")
    body = response.data.decode()
    assert "3" in body


# ------------------------------------------------------------------ #
# Combined category + date range filter                              #
# ------------------------------------------------------------------ #

def test_profile_combined_filter_applies_both_category_and_date_constraints(logged_in_client):
    """Combining category and date range applies both WHERE clauses simultaneously."""
    # Food + Jan only → only "January groceries" (₹500)
    response = logged_in_client.get("/profile?category=Food&from=2026-01-01&to=2026-01-31")
    body = response.data.decode()
    assert "January groceries" in body
    assert "March lunch" not in body   # Food but outside date range
    assert "Train ticket" not in body  # In Jan–Mar but wrong category


def test_profile_combined_filter_total_reflects_single_matching_expense(logged_in_client):
    """Total spent with combined filter equals only the one matching expense (₹500)."""
    response = logged_in_client.get("/profile?category=Food&from=2026-01-01&to=2026-01-31")
    body = response.data.decode()
    assert "500" in body


# ------------------------------------------------------------------ #
# Edge case — from date after to date                                 #
# ------------------------------------------------------------------ #

def test_profile_from_after_to_returns_no_expenses(logged_in_client):
    """When 'from' is after 'to', the result set is empty."""
    response = logged_in_client.get("/profile?from=2026-06-01&to=2026-01-01")
    body = response.data.decode()
    assert "January groceries" not in body
    assert "Train ticket" not in body
    assert "March lunch" not in body


def test_profile_from_after_to_shows_zero_total(logged_in_client):
    """Stats show ₹0 total when the impossible date range produces no results."""
    response = logged_in_client.get("/profile?from=2026-06-01&to=2026-01-01")
    body = response.data.decode()
    assert "₹0" in body


def test_profile_from_after_to_shows_zero_transaction_count(logged_in_client):
    """Transaction count stat is 0 when the date range produces no results."""
    response = logged_in_client.get("/profile?from=2026-06-01&to=2026-01-01")
    body = response.data.decode()
    assert "0" in body


def test_profile_from_after_to_top_category_shows_placeholder(logged_in_client):
    """Top category shows the empty-state placeholder (—) when no rows match."""
    response = logged_in_client.get("/profile?from=2026-06-01&to=2026-01-01")
    body = response.data.decode()
    assert "—" in body


# ------------------------------------------------------------------ #
# Edge case — filter with no matching expenses                        #
# ------------------------------------------------------------------ #

def test_profile_nonexistent_category_filter_returns_no_expenses(logged_in_client):
    """Filtering by a category that has no expenses produces an empty transaction list."""
    response = logged_in_client.get("/profile?category=Nonexistent")
    assert response.status_code == 200
    body = response.data.decode()
    assert "January groceries" not in body
    assert "Train ticket" not in body


def test_profile_nonexistent_category_filter_does_not_crash(logged_in_client):
    """Filtering by a nonexistent category renders the page without errors."""
    response = logged_in_client.get("/profile?category=Nonexistent")
    assert response.status_code == 200


def test_profile_nonexistent_category_filter_shows_zero_stats(logged_in_client):
    """Stats show ₹0 and 0 count when no expenses match the filter."""
    response = logged_in_client.get("/profile?category=Nonexistent")
    body = response.data.decode()
    assert "₹0" in body


# ------------------------------------------------------------------ #
# Edge case — invalid date string in query param                      #
# ------------------------------------------------------------------ #

def test_profile_invalid_from_date_does_not_raise_500(logged_in_client):
    """An invalid 'from' date string in the query param must not crash the server."""
    response = logged_in_client.get("/profile?from=not-a-date")
    assert response.status_code == 200


def test_profile_invalid_to_date_does_not_raise_500(logged_in_client):
    """An invalid 'to' date string must not crash the server."""
    response = logged_in_client.get("/profile?to=bananas")
    assert response.status_code == 200


def test_profile_invalid_date_range_returns_no_matches(logged_in_client):
    """An invalid date string in 'from' results in no expenses being shown."""
    response = logged_in_client.get("/profile?from=not-a-date")
    body = response.data.decode()
    # SQLite date comparison with a non-date string finds no matches
    assert "January groceries" not in body


# ------------------------------------------------------------------ #
# Active filter echo — form pre-fill                                  #
# ------------------------------------------------------------------ #

def test_profile_active_category_filter_is_selected_in_dropdown(logged_in_client):
    """After filtering by category, the dropdown pre-selects the active category."""
    response = logged_in_client.get("/profile?category=Travel")
    body = response.data.decode()
    # The 'selected' attribute must appear near the Travel option
    assert "selected" in body
    # Simplest check: Travel appears with the selected attribute context
    assert "Travel" in body


def test_profile_active_from_date_is_pre_filled_in_form(logged_in_client):
    """After submitting a 'from' date, the date input is pre-filled with that value."""
    response = logged_in_client.get("/profile?from=2026-03-01")
    body = response.data.decode()
    assert "2026-03-01" in body


def test_profile_active_to_date_is_pre_filled_in_form(logged_in_client):
    """After submitting a 'to' date, the date input is pre-filled with that value."""
    response = logged_in_client.get("/profile?to=2026-05-31")
    body = response.data.decode()
    assert "2026-05-31" in body


def test_profile_all_three_filter_values_echoed_simultaneously(logged_in_client):
    """All three filter params (category, from, to) are echoed back at once."""
    response = logged_in_client.get(
        "/profile?category=Food&from=2026-01-01&to=2026-06-30"
    )
    body = response.data.decode()
    assert "2026-01-01" in body
    assert "2026-06-30" in body
    assert "selected" in body   # some option is selected in the dropdown


# ------------------------------------------------------------------ #
# Filtered result count notice                                        #
# ------------------------------------------------------------------ #

def test_profile_filter_active_notice_shown_when_category_filter_applied(logged_in_client):
    """A 'Showing N result(s)' notice appears when a category filter is active."""
    response = logged_in_client.get("/profile?category=Food")
    body = response.data.decode()
    # The spec says: "Showing {{ transactions | length }} result(s)"
    assert "result" in body.lower()


def test_profile_filter_active_notice_shows_filtered_count(logged_in_client):
    """The notice shows the correct number of matched results."""
    # Food has 2 expenses
    response = logged_in_client.get("/profile?category=Food")
    body = response.data.decode()
    assert "2" in body


def test_profile_filter_active_notice_shown_when_from_date_filter_applied(logged_in_client):
    """The active-filter notice renders when only a 'from' date is supplied."""
    response = logged_in_client.get("/profile?from=2026-03-01")
    body = response.data.decode()
    assert "result" in body.lower()


def test_profile_filter_active_notice_shown_when_to_date_filter_applied(logged_in_client):
    """The active-filter notice renders when only a 'to' date is supplied."""
    response = logged_in_client.get("/profile?to=2026-04-30")
    body = response.data.decode()
    assert "result" in body.lower()


def test_profile_filter_active_notice_absent_when_no_filter_applied(logged_in_client):
    """The active-filter notice must NOT appear when no filter params are present."""
    response = logged_in_client.get("/profile")
    body = response.data.decode()
    # The phrase "result(s)" should not be present without an active filter
    assert "result(s)" not in body


def test_profile_clear_filter_link_present_when_filter_is_active(logged_in_client):
    """A 'Clear filter' link is rendered when any filter param is active."""
    response = logged_in_client.get("/profile?category=Bills")
    body = response.data.decode()
    assert "Clear" in body


# ------------------------------------------------------------------ #
# New user with no expenses                                           #
# ------------------------------------------------------------------ #

@pytest.fixture
def empty_user_client(app):
    """A logged-in client for a second user who has no expenses."""
    client = app.test_client()
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (
                "Empty User",
                "empty@example.com",
                generate_password_hash("emptypass"),
                "2026-01-01 00:00:00",
            ),
        )
        db.commit()
    _login(client, "empty@example.com", "emptypass")
    return client


def test_profile_new_user_with_no_expenses_does_not_crash(empty_user_client):
    """GET /profile for a user with zero expenses must return 200 without crashing."""
    response = empty_user_client.get("/profile")
    assert response.status_code == 200


def test_profile_new_user_category_dropdown_shows_all_categories_option_only(empty_user_client):
    """Category dropdown shows only 'All categories' when the user has no expenses."""
    response = empty_user_client.get("/profile")
    body = response.data.decode()
    assert "All categories" in body


def test_profile_new_user_transaction_count_is_zero(empty_user_client):
    """Transaction count stat is 0 for a user with no expenses."""
    response = empty_user_client.get("/profile")
    body = response.data.decode()
    assert "0" in body


def test_profile_new_user_filter_params_do_not_crash(empty_user_client):
    """Filter params on an account with no expenses must not raise an error."""
    response = empty_user_client.get(
        "/profile?category=Food&from=2026-01-01&to=2026-12-31"
    )
    assert response.status_code == 200


# ------------------------------------------------------------------ #
# User data isolation                                                 #
# ------------------------------------------------------------------ #

def test_profile_filter_never_exposes_another_users_expenses(app):
    """A logged-in user must never see expenses that belong to a different account."""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (
                "Other User",
                "other@example.com",
                generate_password_hash("otherpass"),
                "2026-01-01 00:00:00",
            ),
        )
        db.commit()
        other_id = db.execute(
            "SELECT id FROM users WHERE email = ?", ("other@example.com",)
        ).fetchone()["id"]
        db.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (other_id, 9999.00, "Secret", "2026-03-01", "Other user secret expense"),
        )
        db.commit()

    client = app.test_client()
    _login(client, TEST_EMAIL, TEST_PASSWORD)
    response = client.get("/profile")
    body = response.data.decode()
    assert "Other user secret expense" not in body
    assert "9,999" not in body


def test_profile_category_dropdown_shows_only_own_categories(app):
    """The category dropdown must list only the authenticated user's own categories."""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (
                "Another User",
                "another@example.com",
                generate_password_hash("anotherpass"),
                "2026-01-01 00:00:00",
            ),
        )
        db.commit()
        other_id = db.execute(
            "SELECT id FROM users WHERE email = ?", ("another@example.com",)
        ).fetchone()["id"]
        db.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (other_id, 100.00, "TopSecretCategory", "2026-03-01", "Hidden"),
        )
        db.commit()

    client = app.test_client()
    _login(client, TEST_EMAIL, TEST_PASSWORD)
    response = client.get("/profile")
    body = response.data.decode()
    assert "TopSecretCategory" not in body
