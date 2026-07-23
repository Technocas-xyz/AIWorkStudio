"""AI Work Studio - Local development entry point (SQLite)."""

import os
os.environ["APP_ENV"] = "local"

# Now import main app - it will pick up local settings
from app.main import app  # noqa: F401
