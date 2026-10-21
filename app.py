"""
app.py
------
Root application runner and WSGI entry point for Gunicorn / Render deployment.
Supports production Gunicorn: `gunicorn app:app --bind 0.0.0.0:$PORT`
and local development: `python app.py`.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app
from backend.models.database_models import db

# Module-level app instance for Gunicorn WSGI server
env = os.environ.get("FLASK_ENV", "production")
app = create_app(env)

# Ensure database tables exist upon startup
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting server on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=(env == "development"))
