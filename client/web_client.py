"""Flask web client entrypoint for HabitHub.

Implements a hypermedia client for the HabitHub API following patterns from:
https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/exercise-4-implementing-hypermedia-clients/

Usage:
    python web_client.py [--api-url URL] [--api-key KEY] [--port PORT]

Split architecture:
- webapp/api_client.py: HTTP helpers and API error handling.
- webapp/auth.py: login/register/logout and session decorator.
- webapp/routes_habits.py: dashboard, tracking, habits, reminders.
- webapp/routes_settings.py: settings profile and account deletion flow.
- webapp/helpers.py: form parsing and analytics helpers.
- webapp/core.py: Flask app object and runtime API config.

AI-Generated Components (ChatGPT 5.4):
- Initial Flask app scaffolding and route structure.
- Jinja template skeleton (base.html, login.html, dashboard.html, etc.).
- Habit/reminder/tracking CRUD form layouts.
"""

import argparse
import webbrowser
from threading import Timer

from webapp import app, set_api_config


def main() -> None:
    """Parse CLI arguments, optionally open the browser, and start the server."""
    parser = argparse.ArgumentParser(
        description="HabitHub Web Client",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:5000",
        help="Base URL of the HabitHub API server",
    )
    parser.add_argument(
        "--api-key",
        default="aleem",
        help="API key (sent as X-API-KEY header)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5001,
        help="Port to run this web client on",
    )
    args = parser.parse_args()

    set_api_config(args.api_url, args.api_key)

    # Open browser after the server has started.
    Timer(1.2, lambda: webbrowser.open(f"http://localhost:{args.port}")).start()

    app.run(port=args.port, debug=False)


if __name__ == "__main__":
    main()
