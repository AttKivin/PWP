"""Shared helper utilities for forms, analytics, and quote retrieval."""

from datetime import date, datetime, timedelta
from functools import lru_cache

import requests
from flask import request


def form_value(name: str) -> str:
    """Read and trim a form value."""
    return request.form.get(name, "").strip()


def form_email(name: str = "email") -> str:
    """Read an email-like form value and normalize casing."""
    return form_value(name).lower()


def log_dates(logs: list) -> set:
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


def summarize_tracking(logs: list) -> dict:
    """Return dashboard metrics for a habit from a single log-date pass."""
    dates = log_dates(logs)
    today = date.today()
    yesterday = today - timedelta(days=1)

    done_today = today in dates

    streak = 0
    if dates:
        sorted_dates = sorted(dates, reverse=True)
        if sorted_dates[0] in (today, yesterday):
            expected = sorted_dates[0]
            for current_date in sorted_dates:
                if current_date == expected:
                    streak += 1
                    expected = current_date - timedelta(days=1)
                else:
                    break

    cutoff7 = today - timedelta(days=7)
    cutoff30 = today - timedelta(days=30)
    days7 = len({logged_day for logged_day in dates if logged_day > cutoff7})
    days30 = len({logged_day for logged_day in dates if logged_day > cutoff30})

    return {
        "done_today": done_today,
        "streak": streak,
        "days7": days7,
        "days30": days30,
    }


@lru_cache(maxsize=1)
def fetch_quote() -> str:
    """Fetch a motivational quote from ZenQuotes (https://zenquotes.io/)."""
    try:
        resp = requests.get("https://zenquotes.io/api/random", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return f'"{data[0]["q"]}" - {data[0]["a"]}'
    except Exception:
        return '"Small steps every day lead to big changes." - Unknown'
