#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python leakfix_mvp/manage.py collectstatic --noinput
python leakfix_mvp/manage.py migrate
