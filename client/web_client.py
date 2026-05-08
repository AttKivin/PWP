"""Flask web client for HabitHub.

Usage:
    python web_client.py [--api-url URL] [--api-key KEY] [--port PORT]

ChatGPT 5.4 was used to generate the initial version of this file and templates

AI prompts:
    - Build Flask routes for login/register with session-based auth and clear flash feedback.
    - Write reusable API helper functions (GET/POST/PUT/DELETE) with timeouts and consistent error handling.
    - Create Jinja templates (base, dashboard, habits, reminders, settings) with simple CRUD forms and redirect flow.
"""

import argparse
import webbrowser
from datetime import date, datetime, timedelta, timezone
from functools import wraps
from threading import Timer

import requests
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

app = Flask(__name__)
app.secret_key = "habithub-client-secret"  # only used for session/flash


# Can be overridden from CLI flags.
API_URL = "http://localhost:5000"
API_KEY = "12345"


def api_headers() -> dict:
    """Return headers required by the HabitHub API."""
    return {"X-API-KEY": API_KEY, "Content-Type": "application/json"}


def _flash_api_error(exc: requests.exceptions.HTTPError) -> None:
    """Show a consistent API error message in the UI."""
    flash(f"API error {exc.response.status_code}: {exc.response.text}", "danger")


def _form_value(name: str) -> str:
    """Read and trim a form value."""
    return request.form.get(name, "").strip()


def _form_email(name: str = "email") -> str:
    """Read an email-like form value and normalize casing."""
    return _form_value(name).lower()

def _api_get(path: str) -> list | dict | None:
    """GET *path* from the HabitHub API; return parsed JSON or None on error."""
    try:
        resp = requests.get(f"{API_URL}{path}", headers=api_headers(), timeout=8)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        flash("Cannot reach the HabitHub server. Is it running?", "danger")
        return None
    except requests.exceptions.HTTPError as exc:
        _flash_api_error(exc)
        return None


def _api_post(path: str, payload: dict) -> str | None:
    """POST *payload* to *path*; return the Location header (new resource URL) or None."""
    try:
        resp = requests.post(
            f"{API_URL}{path}", json=payload, headers=api_headers(), timeout=8
        )
        resp.raise_for_status()
        return resp.headers.get("Location", "")
    except requests.exceptions.ConnectionError:
        flash("Cannot reach the HabitHub server.", "danger")
        return None
    except requests.exceptions.HTTPError as exc:
        _flash_api_error(exc)
        return None


def _api_put(path: str, payload: dict) -> bool:
    """PUT *payload* to *path*; return True on success."""
    try:
        resp = requests.put(
            f"{API_URL}{path}", json=payload, headers=api_headers(), timeout=8
        )
        resp.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        flash("Cannot reach the HabitHub server.", "danger")
        return False
    except requests.exceptions.HTTPError as exc:
        _flash_api_error(exc)
        return False


def _api_delete(path: str) -> bool:
    """DELETE *path*; return True on success."""
    try:
        resp = requests.delete(
            f"{API_URL}{path}", headers=api_headers(), timeout=8
        )
        resp.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        flash("Cannot reach the HabitHub server.", "danger")
        return False
    except requests.exceptions.HTTPError as exc:
        _flash_api_error(exc)
        return False


def _follow_location(location: str) -> dict | None:
    """GET the Location path returned by a POST and return the new object."""
    if not location:
        return None
    if location.startswith("/"):
        return _api_get(location)
    # strip the base url and fetch
    path = "/" + location.split("/", 3)[-1]
    return _api_get(path)


def _log_dates(logs: list) -> set:
    """Return a set of date objects from a list of tracking logs."""
    dates = set()
    for log in logs:
        raw = log.get("log_time", "")
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            dates.add(datetime.fromisoformat(raw).date())
        except ValueError:
            pass
    return dates


def calculate_streak(logs: list) -> int:
    """Return the current consecutive-day streak."""
    if not logs:
        return 0
    dates = sorted(_log_dates(logs), reverse=True)
    today = date.today()
    yesterday = today - timedelta(days=1)
    if not dates or dates[0] not in (today, yesterday):
        return 0
    streak = 0
    expected = dates[0]
    for d in dates:
        if d == expected:
            streak += 1
            expected = d - timedelta(days=1)
        else:
            break
    return streak


def completion_rate(logs: list, days: int = 30) -> float:
    """Return the completion percentage over the last *days* days."""
    if not logs:
        return 0.0
    cutoff = date.today() - timedelta(days=days)
    return len({d for d in _log_dates(logs) if d > cutoff}) / days * 100.0


def is_done_today(logs: list) -> bool:
    """Return True if at least one log entry exists for today."""
    return date.today() in _log_dates(logs)


def fetch_quote() -> str:
    """Fetch a motivational quote from ZenQuotes (https://zenquotes.io/)."""
    try:
        resp = requests.get("https://zenquotes.io/api/random", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return f'"{data[0]["q"]}" — {data[0]["a"]}'
    except Exception:
        return '"Small steps every day lead to big changes." — Unknown'


def login_required(f):
    """Redirect to the login page if no user is stored in the session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/", methods=["GET"])
def login():
    """Show the login / registration page."""
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def do_login():
    """Authenticate user by email and store the user in session."""
    email = _form_email()
    if not email:
        flash("Please enter your email.", "warning")
        return redirect(url_for("login"))

    users = _api_get("/api/users/") or []
    user = next((u for u in users if u.get("email", "").lower() == email), None)
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
        "first_name": _form_value("first_name"),
        "last_name": _form_value("last_name"),
        "email": _form_value("email"),
    }
    location = _api_post("/api/users/", payload)
    if location:
        user = _follow_location(location)
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


@app.route("/dashboard")
@login_required
def dashboard():
    """Main dashboard: habit overview, today's status, streaks, summary."""
    user_id = session["user_id"]
    habits = _api_get(f"/api/users/{user_id}/habits/") or []
    quote = fetch_quote()

    enriched = []
    for h in habits:
        logs = _api_get(f"/api/users/{user_id}/habits/{h['id']}/tracking/") or []
        enriched.append({
            **h,
            "done_today": is_done_today(logs),
            "streak": calculate_streak(logs),
            "rate7": round(completion_rate(logs, 7), 1),
            "rate30": round(completion_rate(logs, 30), 1),
        })

    done_count = sum(1 for h in enriched if h["done_today"])
    best_streak = max((h["streak"] for h in enriched), default=0)
    active_count = sum(1 for h in enriched if h["active"])
    today_str = date.today().strftime("%A, %B %d %Y")

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
    """Log the current time as a tracking entry for *habit_id*."""
    user_id = session["user_id"]
    now_iso = datetime.now(timezone.utc).isoformat()
    location = _api_post(
        f"/api/users/{user_id}/habits/{habit_id}/tracking/",
        {"log_time": now_iso},
    )
    if location:
        flash("Habit logged! Keep it up 🎉", "success")
    return redirect(url_for("dashboard"))


@app.route("/habits")
@login_required
def habits():
    """Habit management page (list, create, edit, delete)."""
    user_id = session["user_id"]
    habit_list = _api_get(f"/api/users/{user_id}/habits/") or []
    return render_template("habits.html", habits=habit_list)


@app.route("/habits/new", methods=["POST"])
@login_required
def create_habit():
    """Create a new habit."""
    user_id = session["user_id"]
    name = _form_value("name")
    if not name:
        flash("Habit name cannot be empty.", "warning")
        return redirect(url_for("habits"))
    location = _api_post(f"/api/users/{user_id}/habits/", {"name": name, "active": True})
    if location:
        flash(f"Habit '{name}' created.", "success")
    return redirect(url_for("habits"))


@app.route("/habits/<int:habit_id>/edit", methods=["POST"])
@login_required
def edit_habit(habit_id):
    """Edit a habit's name and active status."""
    user_id = session["user_id"]
    name = _form_value("name")
    active = request.form.get("active") == "1"
    if not name:
        flash("Habit name cannot be empty.", "warning")
        return redirect(url_for("habits"))
    ok = _api_put(f"/api/users/{user_id}/habits/{habit_id}/", {"name": name, "active": active})
    if ok:
        flash("Habit updated.", "success")
    return redirect(url_for("habits"))


@app.route("/habits/<int:habit_id>/delete", methods=["POST"])
@login_required
def delete_habit(habit_id):
    """Delete a habit and all its data."""
    user_id = session["user_id"]
    ok = _api_delete(f"/api/users/{user_id}/habits/{habit_id}/")
    if ok:
        flash("Habit deleted.", "success")
    return redirect(url_for("habits"))


@app.route("/habits/<int:habit_id>/reminders")
@login_required
def reminders(habit_id):
    """Reminder management page for a specific habit."""
    user_id = session["user_id"]
    habit = _api_get(f"/api/users/{user_id}/habits/{habit_id}/")
    if not habit:
        return redirect(url_for("habits"))
    reminder_list = _api_get(f"/api/users/{user_id}/habits/{habit_id}/reminders/") or []
    return render_template("reminders.html", habit=habit, reminders=reminder_list)


@app.route("/habits/<int:habit_id>/reminders/new", methods=["POST"])
@login_required
def create_reminder(habit_id):
    """Add a new reminder to a habit."""
    user_id = session["user_id"]
    reminded_time = _form_value("reminded_time")
    location = _api_post(
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
    reminded_time = _form_value("reminded_time")
    ok = _api_put(
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
    ok = _api_delete(f"/api/users/{user_id}/habits/{habit_id}/reminders/{reminder_id}/")
    if ok:
        flash("Reminder deleted.", "success")
    return redirect(url_for("reminders", habit_id=habit_id))


@app.route("/stats")
@login_required
def stats():
    """Statistics page: per-habit analytics, bar charts, and insights."""
    user_id = session["user_id"]
    habits = _api_get(f"/api/users/{user_id}/habits/") or []

    rows = []
    for h in habits:
        logs = _api_get(f"/api/users/{user_id}/habits/{h['id']}/tracking/") or []
        r7 = round(completion_rate(logs, 7), 1)
        r30 = round(completion_rate(logs, 30), 1)
        rows.append({
            **h,
            "streak": calculate_streak(logs),
            "rate7": r7,
            "rate30": r30,
            "total_logs": len(logs),
        })

    best = max(rows, key=lambda r: r["rate30"], default=None)
    worst = min(rows, key=lambda r: r["rate30"], default=None)
    if best and worst and best["id"] == worst["id"]:
        worst = None

    return render_template("stats.html", rows=rows, best=best, worst=worst)


@app.route("/settings")
@login_required
def settings():
    """User settings page."""
    user_id = session["user_id"]
    user = _api_get(f"/api/users/{user_id}/")
    return render_template("settings.html", user=user)


def _delete_account_tree(user_id: int) -> bool:
    """Delete reminders, tracking logs, habits, then the user.

    The API's direct user deletion currently fails when dependent records exist,
    so the client performs the cleanup explicitly.
    """
    habits = _api_get(f"/api/users/{user_id}/habits/") or []
    if habits is None:
        return False

    for habit in habits:
        habit_id = habit["id"]

        reminders = _api_get(f"/api/users/{user_id}/habits/{habit_id}/reminders/") or []
        if reminders is None:
            return False
        for reminder in reminders:
            if not _api_delete(
                f"/api/users/{user_id}/habits/{habit_id}/reminders/{reminder['id']}/"
            ):
                return False

        tracking_logs = _api_get(f"/api/users/{user_id}/habits/{habit_id}/tracking/") or []
        if tracking_logs is None:
            return False
        for tracking in tracking_logs:
            if not _api_delete(
                f"/api/users/{user_id}/habits/{habit_id}/tracking/{tracking['id']}/"
            ):
                return False

        if not _api_delete(f"/api/users/{user_id}/habits/{habit_id}/"):
            return False

    return _api_delete(f"/api/users/{user_id}/")


@app.route("/settings/edit", methods=["POST"])
@login_required
def edit_user():
    """Update the current user's profile."""
    user_id = session["user_id"]
    payload = {
        "first_name": _form_value("first_name"),
        "last_name": _form_value("last_name"),
        "email": _form_value("email"),
    }
    ok = _api_put(f"/api/users/{user_id}/", payload)
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


def main() -> None:
    """Parse CLI arguments, optionally open the browser, and start the server."""
    parser = argparse.ArgumentParser(
        description="HabitHub Web Client",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--api-url", default="http://localhost:5000",
                        help="Base URL of the HabitHub API server")
    parser.add_argument("--api-key", default="aleem",
                        help="API key (sent as X-API-KEY header)")
    parser.add_argument("--port", type=int, default=5001,
                        help="Port to run this web client on")
    args = parser.parse_args()

    global API_URL, API_KEY  # noqa: PLW0603
    API_URL = args.api_url
    API_KEY = args.api_key

    # Open browser after the server has started
    Timer(1.2, lambda: webbrowser.open(f"http://localhost:{args.port}")).start()

    app.run(port=args.port, debug=False)


if __name__ == "__main__":
    main()
