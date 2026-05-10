"""Authentication route group for the split HabitHub client.

Structure citation:
- Moved from the original single-file client into a dedicated auth module.

AI prompt reference (ChatGPT 5.4, summarized):
- "Build login/register/logout routes with Flask session auth and user feedback
    through flash messages."

Manual refinement:
- Fresh-login behavior clears stale sessions on the sign-in page.
"""

from functools import wraps

from flask import flash, redirect, render_template, session, url_for

from .api_client import api_get, api_post, follow_location
from .core import app
from .helpers import form_email, form_value


def login_required(func):
    """Redirect to the login page if no user is stored in the session."""

    @wraps(func)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return decorated


# AI-generated origin (ChatGPT 5.4, prompt 1):
# "Build Flask routes for login/register with session-based auth and flash feedback."
@app.route("/", methods=["GET"])
def login():
    """Show the login / registration page.

    Fresh-login rule: if a prior session exists, clear it when loading the
    sign-in screen so the next user must authenticate again.
    """
    if "user_id" in session:
        session.clear()
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def do_login():
    """Authenticate user by email and store the user in session."""
    email = form_email()
    if not email:
        flash("Please enter your email.", "warning")
        return redirect(url_for("login"))

    users = api_get("/api/users/") or []
    user = next((entry for entry in users if entry.get("email", "").lower() == email), None)
    if not user:
        flash("No account found with that email.", "danger")
        return redirect(url_for("login"))

    session["user_id"] = user["id"]
    session["user_name"] = f"{user['first_name']} {user['last_name']}"
    flash(f"Welcome back, {user['first_name']}.", "success")
    return redirect(url_for("dashboard"))


@app.route("/users/new", methods=["POST"])
def create_user():
    """Create a new user via the API and log them in."""
    payload = {
        "first_name": form_value("first_name"),
        "last_name": form_value("last_name"),
        "email": form_value("email"),
    }
    location = api_post("/api/users/", payload)
    if location:
        user = follow_location(location)
        if user:
            session["user_id"] = user["id"]
            session["user_name"] = f"{user['first_name']} {user['last_name']}"
            flash("Account created successfully!", "success")
            return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    """Clear the session and return to the login page."""
    session.clear()
    return redirect(url_for("login"))
