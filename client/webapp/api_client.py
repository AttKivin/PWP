"""HTTP API helper layer for the HabitHub web client.

Structure citation:
- Split from the original single-file client to centralize request behavior.

Course reference:
- https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/exercise-4-implementing-hypermedia-clients/

AI prompt reference (ChatGPT 5.4, summarized):
- "Write reusable API helper functions (GET/POST/PUT/DELETE) with timeouts and
    consistent error handling."

Manual refinement:
- Flash message policy and Location-follow behavior were adjusted for this app.
"""

import requests
from flask import flash

from . import core


# AI-generated origin (ChatGPT 5.4, prompt 2):
# "Write reusable API helper functions (GET/POST/PUT/DELETE)
# with timeouts and consistent error handling."
def api_headers() -> dict:
    """Return headers required by the HabitHub API.

    Course material reference:
    https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/exercise-4-implementing-hypermedia-clients/#using-requests-sessions
    Sessions can set persistent headers which is helpful for sending Accept and authentication headers.
    """
    return {"X-API-KEY": core.API_KEY, "Content-Type": "application/json"}


def _flash_api_error(exc: requests.exceptions.HTTPError) -> None:
    """Show a consistent API error message in the UI.

    Course material reference:
    https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/exercise-4-implementing-hypermedia-clients/#using-requests
    HTTP error handling is crucial for robust API clients. This helper centralizes error display.
    """
    flash(f"API error {exc.response.status_code}: {exc.response.text}", "danger")


def api_get(path: str) -> list | dict | None:
    """GET *path* from the HabitHub API; return parsed JSON or None on error.

    Course material reference:
    https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/exercise-4-implementing-hypermedia-clients/#using-requests
    'The basic use of Requests is quite simple and very similar to using Flask's test client.
    Like the test client, Requests also has a function for each HTTP method.'

    Follows course pattern:
    - Uses timeout to prevent hanging requests
    - Separates ConnectionError from HTTPError for different error messages
    - Returns parsed JSON on success, None on error
    """
    try:
        resp = requests.get(f"{core.API_URL}{path}", headers=api_headers(), timeout=8)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        flash("Cannot reach the HabitHub server. Is it running?", "danger")
        return None
    except requests.exceptions.HTTPError as exc:
        _flash_api_error(exc)
        return None


def api_post(path: str, payload: dict) -> str | None:
    """POST *payload* to *path*; return the Location header (new resource URL) or None.

    Course material reference:
    https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/exercise-4-implementing-hypermedia-clients/#using-requests
    'Here is how to send a POST request, and read the Location header afterward'

    Returns the Location header from the response, which points to the newly created resource.
    """
    try:
        resp = requests.post(
            f"{core.API_URL}{path}", json=payload, headers=api_headers(), timeout=8
        )
        resp.raise_for_status()
        return resp.headers.get("Location", "")
    except requests.exceptions.ConnectionError:
        flash("Cannot reach the HabitHub server.", "danger")
        return None
    except requests.exceptions.HTTPError as exc:
        _flash_api_error(exc)
        return None


def api_put(path: str, payload: dict) -> bool:
    """PUT *payload* to *path*; return True on success.

    Course material reference:
    https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/exercise-4-implementing-hypermedia-clients/#using-requests
    Generic client methods for each HTTP method (GET, POST, PUT, DELETE) enable unified request handling.

    PUT is idempotent and used for full resource updates.
    """
    try:
        resp = requests.put(
            f"{core.API_URL}{path}", json=payload, headers=api_headers(), timeout=8
        )
        resp.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        flash("Cannot reach the HabitHub server.", "danger")
        return False
    except requests.exceptions.HTTPError as exc:
        _flash_api_error(exc)
        return False


def api_delete(path: str) -> bool:
    """DELETE *path*; return True on success.

    Course material reference:
    https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/exercise-4-implementing-hypermedia-clients/
    DELETE requests are used to remove resources. Like other methods, they are wrapped with
    consistent error handling and user feedback through Flask flash messages.
    """
    try:
        resp = requests.delete(f"{core.API_URL}{path}", headers=api_headers(), timeout=8)
        resp.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        flash("Cannot reach the HabitHub server.", "danger")
        return False
    except requests.exceptions.HTTPError as exc:
        _flash_api_error(exc)
        return False


def follow_location(location: str) -> dict | None:
    """GET the Location path returned by a POST and return the new object."""
    if not location:
        return None
    if location.startswith("/"):
        return api_get(location)
    path = "/" + location.split("/", 3)[-1]
    return api_get(path)
