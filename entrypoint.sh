#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Apply database migrations
echo "Applying database migrations..."
python leakfix_mvp/manage.py migrate --no-input

# Start the Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:8000 --chdir leakfix_mvp leakfix.wsgi:application
