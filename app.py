# app.py — top-level Flask entrypoint for Vercel detection
# Imports the Flask `app` defined in server/app.py and re-exports it.
# Vercel's detector looks for a top-level file with `app`/`application` etc.
from server.app import app  # noqa: E402,F401
