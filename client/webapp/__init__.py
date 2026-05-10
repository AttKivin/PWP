"""Webapp package bootstrap for the split HabitHub client structure.

Structure citation:
- This package-level initializer was introduced during the split from a single
	`web_client.py` file into modular components.

AI prompt reference (ChatGPT 5.4, summarized):
- "Refactor a monolithic Flask client into focused modules and keep the public
	 entrypoint unchanged."

Manual refinement:
- Route import ordering and exported symbols were adjusted by hand.
"""

from .core import app, set_api_config

# Register all routes via import side effects.
from . import auth as _auth_routes  # noqa: F401
from . import routes_habits as _habit_routes  # noqa: F401
from . import routes_settings as _settings_routes  # noqa: F401

__all__ = ["app", "set_api_config"]
