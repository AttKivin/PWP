"""Static HabitHub web client entrypoint"""

import argparse
from pathlib import Path
import webbrowser
from threading import Timer

import requests
from flask import Flask, Response, request, send_from_directory


STATIC_DIR = Path(__file__).resolve().parent / "static"
app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")
API_URL = "http://localhost:5000"
API_KEY = "aleem"


def set_api_config(api_url: str, api_key: str) -> None:
    """Set runtime configuration for the proxied API endpoint and API key."""
    global API_URL, API_KEY
    API_URL = api_url.rstrip("/")
    API_KEY = api_key


def _proxy_headers() -> dict:
    """Build upstream headers for the proxied request."""
    headers = {
        "X-API-KEY": request.headers.get("X-API-KEY", API_KEY),
    }
    if request.headers.get("Content-Type"):
        headers["Content-Type"] = request.headers["Content-Type"]
    if request.headers.get("Accept"):
        headers["Accept"] = request.headers["Accept"]
    return headers


@app.route("/api/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def proxy_api(path: str):
    """Forward API traffic to the configured backend server."""
    base = f"{API_URL}/api"
    target = f"{base}/{path}" if path else f"{base}/"
    try:
        upstream = requests.request(
            method=request.method,
            url=target,
            params=request.args,
            data=request.get_data() if request.method in {"POST", "PUT", "PATCH"} else None,
            headers=_proxy_headers(),
            timeout=10,
            allow_redirects=False,
        )
    except requests.RequestException:
        return Response(
            '{"message":"Cannot reach HabitHub API server."}',
            status=502,
            mimetype="application/json",
        )

    excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    response_headers = [(k, v) for k, v in upstream.headers.items() if k.lower() not in excluded]
    return Response(upstream.content, status=upstream.status_code, headers=response_headers)


@app.route("/")
def root():
    """Serve the static login page as the default entrypoint."""
    return send_from_directory(str(STATIC_DIR), "login.html")


@app.route("/<path:path>")
def serve_static(path: str):
    """Serve static client assets and pages."""
    file_path = STATIC_DIR / path
    if file_path.exists() and file_path.is_file():
        return send_from_directory(str(STATIC_DIR), path)
    return send_from_directory(str(STATIC_DIR), "login.html")


def main() -> None:
    """Parse CLI arguments, open browser, and run static client server."""
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
