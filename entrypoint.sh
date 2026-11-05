#!/bin/sh
set -e

cd /app/django

python /app/wait_for_db.py
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py createsuperuser_if_not_exists

exec gunicorn italiaans.wsgi:application -c /app/gunicorn.conf.py
