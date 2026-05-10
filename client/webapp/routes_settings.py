"""Settings and account-management routes for the split HabitHub client"""

from flask import flash, redirect, render_template, session, url_for

from .api_client import api_delete, api_get, api_put
from .auth import login_required
from .core import app
from .helpers import form_value


@app.route("/settings")
@login_required
def settings():
    """User settings page.

    Retrieves and displays the user's profile.
    """
    user_id = session["user_id"]
    user = api_get(f"/api/users/{user_id}/")
    return render_template("settings.html", user=user)


def _delete_account_tree(user_id: int) -> bool:
    """Delete reminders, tracking logs, habits, then the user.

    The API's direct user deletion currently fails when dependent records exist,
    so the client performs the cleanup explicitly. 
    """
    habits = api_get(f"/api/users/{user_id}/habits/") or []
    if habits is None:
        return False

    for habit in habits:
        habit_id = habit["id"]

        reminders = api_get(f"/api/users/{user_id}/habits/{habit_id}/reminders/") or []
        if reminders is None:
            return False
        for reminder in reminders:
            if not api_delete(
                f"/api/users/{user_id}/habits/{habit_id}/reminders/{reminder['id']}/"
            ):
                return False

        tracking_logs = api_get(f"/api/users/{user_id}/habits/{habit_id}/tracking/") or []
        if tracking_logs is None:
            return False
        for tracking in tracking_logs:
            if not api_delete(
                f"/api/users/{user_id}/habits/{habit_id}/tracking/{tracking['id']}/"
            ):
                return False

        if not api_delete(f"/api/users/{user_id}/habits/{habit_id}/"):
            return False

    return api_delete(f"/api/users/{user_id}/")


@app.route("/settings/edit", methods=["POST"])
@login_required
def edit_user():
    """Update the current user's profile"""
    
    user_id = session["user_id"]
    payload = {
        "first_name": form_value("first_name"),
        "last_name": form_value("last_name"),
        "email": form_value("email"),
    }
    ok = api_put(f"/api/users/{user_id}/", payload)
    if ok:
        session["user_name"] = f"{payload['first_name']} {payload['last_name']}"
        flash("Profile updated.", "success")
    return redirect(url_for("settings"))


@app.route("/settings/delete", methods=["POST"])
@login_required
def delete_user():
    """Delete the current user's account."""
    user_id = session["user_id"]
    ok = _delete_account_tree(user_id)
    if ok:
        session.clear()
        flash("Account deleted.", "info")
    else:
        flash("Could not delete the account and all related data.", "danger")
    return redirect(url_for("login"))
