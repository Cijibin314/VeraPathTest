#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

cd leakfix_mvp
python manage.py collectstatic --noinput
python manage.py migrate
