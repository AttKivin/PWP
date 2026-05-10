"""Core Flask app object and runtime API configuration"""

from flask import Flask

app = Flask(__name__, template_folder="../templates")
app.secret_key = "habithub-client-secret"  # only used for session/flash

# Runtime API config overridden via CLI in web_client.py.
API_URL = "http://localhost:5000"
API_KEY = "12345"


def set_api_config(api_url: str, api_key: str) -> None:
    """Update API runtime configuration from CLI args."""
    global API_URL, API_KEY
    API_URL = api_url
    API_KEY = api_key
