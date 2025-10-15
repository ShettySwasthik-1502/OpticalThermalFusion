# api/app.py
# This file is the Vercel entrypoint. Vercel's Python runtime will look for
# a variable named `app` that exposes a WSGI or ASGI application.
# We re-use the Flask app defined in server/app.py (the file you already provided).

from server.app import app  # `app` is the Flask instance in server/app.py

# Vercel will detect this `app` variable and run it as a WSGI app.
# No additional code required here.
