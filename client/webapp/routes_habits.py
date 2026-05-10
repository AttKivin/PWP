"""Habit, reminder, tracking, and dashboard routes.

Structure citation:
- This feature route group was split from the original monolithic client file.

AI prompt reference (ChatGPT 5.4, summarized):
- "Create grouped Flask routes for dashboard, habits, reminders, and tracking,
  then keep business helpers reusable."

Manual refinement:
- The dashboard now stays lightweight by fetching only the habit collection and
  deriving simple counts from that list.
"""

from datetime import datetime, timezone

from flask import flash, redirect, render_template, session, url_for

from .api_client import api_delete, api_get, api_post, api_put
from .auth import login_required
from .core import app
from .helpers import (
    fetch_quote,
    form_value,
    summarize_tracking,
)


# AI-generated origin (ChatGPT 5.4, prompts 1 and 3):
# Prompt 1: "Build Flask routes for login/register with session-based auth and flash feedback."
# Prompt 3: "Create Jinja templates with simple CRUD forms and redirect flow."
@app.route("/dashboard")
@login_required
def dashboard():
    """Main dashboard: lightweight habit overview and quick actions.

    Implements the hypermedia client pattern for displaying related resources.
    Course reference:
    https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/exercise-4-implementing-hypermedia-clients/#designing-hypermedia-clients
    'The client can follow links and fetch related resource representations...'

    Hand-written implementation: Keeps the dashboard lightweight by fetching
    only the habit collection and deriving simple counts from that list.
    """
    user_id = session["user_id"]
    habits = api_get(f"/api/users/{user_id}/habits/") or []
    quote = fetch_quote()
    active_count = sum(1 for habit in habits if habit["active"])
    today_str = datetime.now(timezone.utc).strftime("%A, %B %d %Y")
    enriched = []

    for habit in habits:
        logs = api_get(f"/api/users/{user_id}/habits/{habit['id']}/tracking/") or []
        metrics = summarize_tracking(logs)
        enriched.append(
            {
                **habit,
                **metrics,
            }
        )

    done_count = sum(1 for habit in enriched if habit["done_today"])
    best_streak = max((habit["streak"] for habit in enriched), default=0)

    return render_template(
        "dashboard.html",
        habits=enriched,
        quote=quote,
        done_count=done_count,
        best_streak=best_streak,
        active_count=active_count,
        today_str=today_str,
        total=len(habits),
    )


@app.route("/track/<int:habit_id>", methods=["POST"])
@login_required
def track_habit(habit_id):
    """Log the current time as a tracking entry for *habit_id*.

    Demonstrates POST for resource creation and Location header following.
    Course reference:
    https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/exercise-4-implementing-hypermedia-clients/#the-post-method
    'When successful, POST returns a 201 Created response with a Location header...'
    'The client can use the Location header to retrieve or work with the newly created resource.'

    Hand-written pattern: posts UTC timestamp and redirects to dashboard.
    """
    user_id = session["user_id"]
    now_iso = datetime.now(timezone.utc).isoformat()
    location = api_post(
        f"/api/users/{user_id}/habits/{habit_id}/tracking/",
        {"log_time": now_iso},
    )
    if location:
        flash("Habit logged! Keep it up!", "success")
    return redirect(url_for("dashboard"))


@app.route("/habits")
@login_required
def habits():
    """Habit management page (list, create, edit, delete).

    Fetches and displays a collection of habit resources.
    Course reference:
    https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/exercise-4-implementing-hypermedia-clients/#the-get-method
    'The client can retrieve representations of resources...'
    'Collections are endpoints that return a list of resource representations.'

    Hand-written implementation: Provides CRUD interface for habit lifecycle management.
    """
    user_id = session["user_id"]
    habit_list = api_get(f"/api/users/{user_id}/habits/") or []
    return render_template("habits.html", habits=habit_list)


@app.route("/habits/new", methods=["POST"])
@login_required
def create_habit():
    """Create a new habit."""
    user_id = session["user_id"]
    name = form_value("name")
    if not name:
        flash("Habit name cannot be empty.", "warning")
        return redirect(url_for("habits"))
    location = api_post(f"/api/users/{user_id}/habits/", {"name": name, "active": True})
    if location:
        flash(f"Habit '{name}' created.", "success")
    return redirect(url_for("habits"))


@app.route("/habits/<int:habit_id>/edit", methods=["POST"])
@login_required
def edit_habit(habit_id):
    """Edit a habit's name and active status."""
    user_id = session["user_id"]
    name = form_value("name")
    active = form_value("active") == "1"
    if not name:
        flash("Habit name cannot be empty.", "warning")
        return redirect(url_for("habits"))
    ok = api_put(f"/api/users/{user_id}/habits/{habit_id}/", {"name": name, "active": active})
    if ok:
        flash("Habit updated.", "success")
    return redirect(url_for("habits"))


@app.route("/habits/<int:habit_id>/delete", methods=["POST"])
@login_required
def delete_habit(habit_id):
    """Delete a habit and all its data."""
    user_id = session["user_id"]
    ok = api_delete(f"/api/users/{user_id}/habits/{habit_id}/")
    if ok:
        flash("Habit deleted.", "success")
    return redirect(url_for("habits"))


@app.route("/habits/<int:habit_id>/reminders")
@login_required
def reminders(habit_id):
    """Reminder management page for a specific habit."""
    user_id = session["user_id"]
    habit = api_get(f"/api/users/{user_id}/habits/{habit_id}/")
    if not habit:
        return redirect(url_for("habits"))
    reminder_list = api_get(f"/api/users/{user_id}/habits/{habit_id}/reminders/") or []
    return render_template("reminders.html", habit=habit, reminders=reminder_list)


@app.route("/habits/<int:habit_id>/reminders/new", methods=["POST"])
@login_required
def create_reminder(habit_id):
    """Add a new reminder to a habit."""
    user_id = session["user_id"]
    reminded_time = form_value("reminded_time")
    location = api_post(
        f"/api/users/{user_id}/habits/{habit_id}/reminders/",
        {"reminded_time": reminded_time},
    )
    if location:
        flash(f"Reminder set for {reminded_time}.", "success")
    return redirect(url_for("reminders", habit_id=habit_id))


@app.route("/habits/<int:habit_id>/reminders/<int:reminder_id>/edit", methods=["POST"])
@login_required
def edit_reminder(habit_id, reminder_id):
    """Update a reminder's time."""
    user_id = session["user_id"]
    reminded_time = form_value("reminded_time")
    ok = api_put(
        f"/api/users/{user_id}/habits/{habit_id}/reminders/{reminder_id}/",
        {"reminded_time": reminded_time},
    )
    if ok:
        flash("Reminder updated.", "success")
    return redirect(url_for("reminders", habit_id=habit_id))


@app.route("/habits/<int:habit_id>/reminders/<int:reminder_id>/delete", methods=["POST"])
@login_required
def delete_reminder(habit_id, reminder_id):
    """Delete a reminder."""
    user_id = session["user_id"]
    ok = api_delete(f"/api/users/{user_id}/habits/{habit_id}/reminders/{reminder_id}/")
    if ok:
        flash("Reminder deleted.", "success")
    return redirect(url_for("reminders", habit_id=habit_id))
